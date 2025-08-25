# backend/data/providers/akshare_provider.py
# -*- coding: utf-8 -*-

"""
AkShare 数据提供器
=================
目标：
  - 通过 AkShare 拉取中国 A 股历史日线数据
  - 统一为内部标准格式：索引=交易日(date)；列=open, high, low, close, volume(+ 可选 adj_factor)
  - 自动完成列名重命名、量纲统一（volume→股）、交易日历对齐（XSHG）、停牌日补行、复权处理
  - 简单的超时/重试机制，增强健壮性

依赖：
  - akshare
  - pandas
  - exchange_calendars（由第4步 normalize 流程间接使用）

注意：
  - 目前实现 **日线('1d')**，如需分钟级可在后续扩展
  - 复权策略：
      * 若 adjust='pre'（默认）或 'post'：直接向 AkShare 请求对应口径（qfq/hfq），
        并在“对齐”时传入 adjust='none'（避免二次复权）；
      * 若 adjust='none'：请求未复权口径，仍执行“交易日历对齐+停牌补行”，但不做价格复权。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Literal

import pandas as pd

from backend.data.normalize import (
    to_internal,
    align_and_adjust_ohlcv,
)

# 类型标注：仅支持日线
FreqT = Literal["1d"]
AdjustT = Literal["pre", "post", "none"]


@dataclass
class AkshareProvider:
    """
    AkShare 数据源适配器

    参数：
      calendar_name : 交易日历名称，默认 'XSHG'（上交所，兼容深沪统一交易日）
      timeout       : 单次请求超时（秒），AkShare 内部依赖网络，视环境设置
      retries       : 失败重试次数
      retry_sleep   : 重试前等待时间（秒）
      default_exchange : 当传入代码无法推断交易所时，回退交易所（默认 'XSHE'）
      volume_unit   : 成交量单位转换，'hands' 表示原始为“手”，转换为“股”需 x100；'shares' 表示已为“股”
    """
    calendar_name: str = "XSHG"
    timeout: float = 15.0
    retries: int = 3
    retry_sleep: float = 0.8
    default_exchange: str = "XSHE"
    volume_unit: Literal["hands", "shares"] = "hands"

    # ---- 内部：AkShare 接口名与复权口径映射 ----
    _AK_ADJUST_MAP = {
        "pre": "qfq",   # 前复权
        "post": "hfq",  # 后复权
        "none": "",     # 不复权
    }

    def _ak_import(self):
        """延迟导入 akshare，避免环境未安装时在其它流程中就报错。"""
        try:
            import akshare as ak  # type: ignore
            return ak
        except Exception as e:
            raise RuntimeError(
                "未能导入 akshare，请先安装：pip install akshare"
            ) from e

    @staticmethod
    def _date_to_ak(s: str | pd.Timestamp) -> str:
        """将日期转换为 AkShare 常用的 YYYYMMDD 字符串。"""
        ts = pd.Timestamp(s)
        return ts.strftime("%Y%m%d")

    def _fetch_daily_core(
        self,
        symbol_internal: str,
        start: str,
        end: str,
        adjust: AdjustT,
    ) -> pd.DataFrame:
        """
        核心抓取函数（仅日线）。
        - 调用 ak.stock_zh_a_hist(symbol=六位代码, period='daily', start_date, end_date, adjust)
        - 返回原始 DataFrame（中文列名），不做对齐与复权（复权已在接口口径完成）
        """
        ak = self._ak_import()
        code6 = symbol_internal.split(".")[0]  # 内部格式如 002415.XSHE -> 002415

        start_ = self._date_to_ak(start)
        end_ = self._date_to_ak(end)
        adj = self._AK_ADJUST_MAP.get(adjust, "")

        last_err: Optional[Exception] = None
        for _ in range(max(1, self.retries)):
            try:
                # AkShare: 东方财富源，常用接口
                # 文档（以当下版本为准）：stock_zh_a_hist(symbol, period, start_date, end_date, adjust)
                df = ak.stock_zh_a_hist(
                    symbol=code6,
                    period="daily",
                    start_date=start_,
                    end_date=end_,
                    adjust=adj,
                )
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df
                last_err = RuntimeError("AkShare 返回空数据")
            except Exception as e:
                last_err = e
            time.sleep(self.retry_sleep)

        # 所有尝试失败
        raise RuntimeError(f"AkShare 拉取失败：symbol={symbol_internal}, err={last_err}")

    @staticmethod
    def _rename_and_scale(df_raw: pd.DataFrame, volume_unit: str) -> pd.DataFrame:
        """
        将 AkShare 的中文列名转换为标准列；并完成成交量量纲统一。
        - 常见列：['日期','开盘','收盘','最高','最低','成交量','成交额','振幅','涨跌幅','涨跌额','换手率']
        - 我们保留并返回：open, high, low, close, volume
        - 成交量单位：
            * 若为“手”(hands)，需 *100 -> 股(shares)
            * 若已为“股”(shares)，则保持不变
        """
        colmap = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            # 可扩展：若返回包含“前复权因子/复权因子”等，可在此接入 adj_factor
        }

        # 1) 仅保留需要的列（存在则重命名）
        cols = {k: v for k, v in colmap.items() if k in df_raw.columns}
        df = df_raw[list(cols.keys())].rename(columns=cols).copy()

        # 2) 基本类型转换
        for c in ("open", "high", "low", "close", "volume"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # 3) 成交量量纲统一
        if "volume" in df.columns:
            if volume_unit == "hands":
                # “手” -> “股”
                df["volume"] = df["volume"] * 100.0
            # 若 volume_unit == "shares" 则不处理

        # 4) 索引设置为日期（日粒度）
        if "date" not in df.columns:
            raise ValueError("AkShare 返回缺少列：'日期'，无法完成重命名为 'date'")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date").sort_index()

        # 5) 去重同日（保险）
        if df.index.has_duplicates:
            df = df.groupby(df.index).agg({
                "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
            })

        return df[["open", "high", "low", "close", "volume"]]

    # ---------- 对外主接口 ----------
    def fetch_ohlcv(
        self,
        symbol: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
        freq: FreqT = "1d",
        adjust: AdjustT = "pre",
    ) -> pd.DataFrame:
        """
        拉取日线 OHLCV，并返回**已标准化**的数据（索引=交易日，列=open,high,low,close,volume）。
        - 已完成：列名统一、量纲统一、交易日历对齐与停牌补行、复权处理（见下）
        - 复权策略：
            * adjust='pre'（默认）或 'post'：直接拉取前/后复权价格；随后对齐时传入 adjust='none'（避免二次复权）
            * adjust='none'：拉取未复权价格；对齐时也传入 adjust='none'
        """
        if freq != "1d":
            raise NotImplementedError("AkshareProvider 当前仅支持日线 freq='1d'")

        # 统一内部代码，补全交易所后缀（若必要）
        internal = to_internal(symbol, default_exchange=self.default_exchange)

        # 1) 原始抓取（按目标复权口径）
        raw = self._fetch_daily_core(internal, str(start), str(end), adjust=adjust)

        # 2) 列名与量纲统一（volume 归一为“股”）
        std = self._rename_and_scale(raw, volume_unit=self.volume_unit)

        # 3) 交易日历对齐 + 停牌补行 + 复权处理：
        #    若已在抓取阶段复了权（pre/hfq），此处应避免再次复权 => adjust='none'
        adj_for_align = "none"

        df_final = align_and_adjust_ohlcv(
            std,
            start=str(start),
            end=str(end),
            calendar_name=self.calendar_name,
            adjust=adj_for_align,   # 避免二次复权
            fill_leading=False      # 不强制齐头；若你用于 bundle，可改为 True
        )

        # 返回最终标准化 DataFrame
        return df_final
