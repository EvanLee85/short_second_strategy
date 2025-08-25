# -*- coding: utf-8 -*-
"""
TuShare 适配器
----------------
用途：
  - 作为备源 / 对比源，按统一接口输出标准的 OHLCV 数据。
  - 支持“前复权（pre）/不复权（none）”两种口径。
  - 对接统一的交易日历与对齐规范（见 normalize.align_and_adjust_ohlcv）。

依赖：
  - pip install tushare
  - 环境变量 TUSHARE_TOKEN（或在构造器传入 token）

返回：
  - pandas.DataFrame，索引为日期（tz-naive），列为 open, high, low, close, volume
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import pandas as pd

from .base import BaseMarketDataProvider
from backend.data.normalize import align_and_adjust_ohlcv


class TuShareProvider(BaseMarketDataProvider):
    """
    TuShare 数据提供器（实现 BaseMarketDataProvider 接口）

    主要职责：
    1）读取 token，创建 pro_api 客户端
    2）调用 daily 与 adj_factor，合成“前复权”价格
    3）标准化列名与量纲（volume：手 -> 股）
    4）交给 normalize.align_and_adjust_ohlcv 做交易日对齐、停牌补行

    仅支持日线（freq="1d"）。其他周期可后续扩展。
    """

    def __init__(
        self,
        token: Optional[str] = None,
        calendar_name: str = "XSHG",
        timeout: float = 10.0,
        max_retries: int = 2,
        retry_sleep: float = 0.8,
    ) -> None:
        """
        参数：
          token         : TuShare 授权 token；若为 None，则从环境变量 TUSHARE_TOKEN 读取
          calendar_name : 交易日历名称（默认 XSHG）
          timeout       : 访问超时时间（秒），用于错误提示（TuShare SDK 无显式超时）
          max_retries   : 失败重试次数
          retry_sleep   : 重试之间的休眠秒数
        """
        self.token = token or os.environ.get("TUSHARE_TOKEN", "").strip()
        if not self.token:
            raise RuntimeError(
                "TuShareProvider 初始化失败：未找到 token。"
                "请在构造参数传入 token，或设置环境变量 TUSHARE_TOKEN。"
            )
        try:
            import tushare as ts  # 延迟导入，便于无依赖环境下通过类型检查
        except Exception as e:  # noqa: BLE001
            raise ImportError(
                "未安装 tushare，请先 `pip install tushare`。"
            ) from e

        # 初始化 TuShare 客户端
        self._ts = ts
        self._pro = ts.pro_api(self.token)

        self.calendar_name = calendar_name
        self.timeout = float(timeout)
        self.max_retries = int(max_retries)
        self.retry_sleep = float(retry_sleep)

    # ------------------------ 工具函数 ------------------------

    @staticmethod
    def _internal_to_ts_code(symbol: str) -> str:
        """
        将内部统一代码（如 002415.XSHE / 600000.XSHG）转换为 TuShare ts_code（002415.SZ / 600000.SH）

        规则：
          - .XSHE -> .SZ
          - .XSHG -> .SH
          - 若无后缀，按“6 开头为上交所，其它为深交所”的宽松推断（仅兜底场景）

        说明：
          - 仅对 A 股常见股票代码做轻量映射；若有更复杂市场，请扩展。
        """
        s = (symbol or "").upper().strip()
        if "." in s:
            code, exch = s.split(".", 1)
            if exch == "XSHE":
                return f"{code}.SZ"
            if exch == "XSHG":
                return f"{code}.SH"
            # 其它后缀，原样返回（或按需扩展映射）
            return s
        # 无后缀：做最小化猜测
        if s.startswith("6"):
            return f"{s}.SH"
        return f"{s}.SZ"

    @staticmethod
    def _yyyymmdd(x: str | pd.Timestamp) -> str:
        """将 'YYYY-MM-DD' 或 Timestamp 统一转为 'YYYYMMDD'（TuShare 接口要求）"""
        ts = pd.Timestamp(x)
        # TuShare 接口不接受带时区的日期字符串，这里去时区
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts.strftime("%Y%m%d")

    @staticmethod
    def _retry_call(fn, max_retries: int = 2, sleep_sec: float = 0.8, **kwargs):
        """简单重试封装：调用 fn(**kwargs)，失败则最多重试 max_retries 次。"""
        attempt = 0
        last_err = None
        while attempt <= max_retries:
            try:
                return fn(**kwargs)
            except Exception as e:  # noqa: BLE001
                last_err = e
                attempt += 1
                if attempt > max_retries:
                    break
                time.sleep(sleep_sec)
        # 所有尝试失败
        raise last_err  # 将最后一次异常抛出

    # ------------------------ 接口实现 ------------------------

    def fetch_ohlcv(
        self,
        symbol: str,
        start: str,
        end: str,
        freq: str = "1d",
        adjust: str = "pre",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        拉取 OHLCV（标准日线），并按统一规则输出。

        参数：
          symbol  : 内部统一代码（如 002415.XSHE）
          start   : 开始日期，'YYYY-MM-DD'
          end     : 结束日期，'YYYY-MM-DD'
          freq    : 目前仅支持 "1d"
          adjust  : 价格口径；"pre"=前复权，"none"=不复权（默认使用“前复权”）
          kwargs  : 预留扩展（暂不用）

        返回：
          DataFrame（index=日期，columns=['open','high','low','close','volume']）
          - 日期为 tz-naive，日粒度
          - volume 单位：股（TuShare daily.vol 为“手”，已 *100）
        """
        if freq != "1d":
            raise NotImplementedError("TuShareProvider 目前仅支持日线 freq='1d'。")

        ts_code = self._internal_to_ts_code(symbol)
        start_yyyymmdd = self._yyyymmdd(start)
        end_yyyymmdd = self._yyyymmdd(end)

        # ---------- 1）取不复权日线 ----------
        # 字段含：trade_date, open, high, low, close, vol（单位：手）, amount（千元）
        df_daily = self._retry_call(
            self._pro.daily,
            max_retries=self.max_retries,
            sleep_sec=self.retry_sleep,
            ts_code=ts_code,
            start_date=start_yyyymmdd,
            end_date=end_yyyymmdd,
        )

        if df_daily is None or df_daily.empty:
            # 返回一个空但结构一致的 DataFrame，避免上游因 None 失败
            empty = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"],
                index=pd.DatetimeIndex([], name=None),
            )
            return empty

        # TuShare 默认按日期降序返回，这里统一升序（时间从旧到新）
        df_daily = df_daily.sort_values("trade_date").reset_index(drop=True)

        # ---------- 2）前复权：用 adj_factor 做口径转换 ----------
        # 规则：前复权价 = 原价 * (adj_factor / 最新 adj_factor)
        # 注：若 choose adjust='none'，则跳过复权，仅做对齐。
        if adjust.lower() == "pre":
            df_adj = self._retry_call(
                self._pro.adj_factor,
                max_retries=self.max_retries,
                sleep_sec=self.retry_sleep,
                ts_code=ts_code,
                start_date=start_yyyymmdd,
                end_date=end_yyyymmdd,
            )
            if df_adj is not None and not df_adj.empty:
                df_adj = df_adj.sort_values("trade_date").reset_index(drop=True)
                # 合并到 daily
                dfm = pd.merge(df_daily, df_adj[["trade_date", "adj_factor"]], on="trade_date", how="left")
                # 若少量日期缺失因子，向前/向后填充（通常不该发生）
                dfm["adj_factor"] = dfm["adj_factor"].ffill().bfill()
                latest = float(dfm["adj_factor"].iloc[-1]) if not dfm["adj_factor"].empty else 1.0
                # 安全兜底，避免除零
                latest = latest if latest != 0 else 1.0
                ratio = dfm["adj_factor"] / latest

                # 调整 OHLC（volume 不复权）
                for col in ["open", "high", "low", "close"]:
                    dfm[col] = pd.to_numeric(dfm[col], errors="coerce") * ratio

                df_used = dfm.copy()
            else:
                # 没拿到因子：退化为不复权（给出轻提示场景）
                df_used = df_daily.copy()
        elif adjust.lower() in ("none", "raw"):
            df_used = df_daily.copy()
        else:
            raise ValueError(f"不支持的 adjust 参数：{adjust}，可选：'pre' 或 'none'。")

        # ---------- 3）重命名与量纲统一 ----------
        # 体积单位：手 -> 股
        df_used["volume"] = pd.to_numeric(df_used.get("vol", 0), errors="coerce").fillna(0) * 100

        df_used = df_used.rename(
            columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
            }
        )

        # 仅保留标准列，并将索引设置为日期（tz-naive）
        df_used["trade_date"] = pd.to_datetime(df_used["trade_date"], format="%Y%m%d", errors="coerce")
        df_used = df_used.set_index("trade_date").sort_index()
        df_used = df_used[["open", "high", "low", "close", "volume"]].astype(float)

        # ---------- 4）统一交易日对齐与停牌补行 ----------
        # 说明：上一步已做“前复权”，此处不再二次复权，故传 adjust="none"
        df_final = align_and_adjust_ohlcv(
            df_used,
            start=start,
            end=end,
            calendar_name=self.calendar_name,
            adjust="none",
            price_cols=("open", "high", "low", "close"),
            volume_col="volume",
        )

        return df_final
