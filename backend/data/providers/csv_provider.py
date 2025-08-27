# -*- coding: utf-8 -*-
"""
CSV / Stub 适配器
-----------------
用途：
  - 在"无网络 / 限流 / 主备源不可用"时，作为兜底数据源；
  - 同时兼容你现有的 CSV 文件与 Zipline 写入路径（如 data/zipline_csv/TEST.csv）；
  - 若找不到 CSV 且允许兜底，则按请求区间生成"可控的桩数据（stub）"。

统一接口：
  fetch_ohlcv(symbol, start, end, freq="1d", adjust="pre"|"none") -> DataFrame
  - 返回列：open, high, low, close, volume
  - 索引：日期（tz-naive，日粒度）
  - 会调用 normalize.align_and_adjust_ohlcv 做"交易日对齐 + 停牌补行"
"""

from __future__ import annotations

import os
import glob
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .base import BaseMarketDataProvider
from backend.data.normalize import align_and_adjust_ohlcv


class CsvProvider(BaseMarketDataProvider):
    """
    CSV / Stub 数据提供器（实现 BaseMarketDataProvider 接口）

    关键能力：
      1）从指定目录读取 CSV（自动识别常见列名与日期列）；
      2）若 CSV 含"复权因子"（如 adj_factor/factor），支持前复权（pre）；
      3）若无复权信息，则在 adjust="none" 下直接返回，或在 adjust="pre" 给出最简近似（等同 none）；
      4）若找不到 CSV 且允许 fallback_stub，则生成区间内的"桩数据"；
      5）统一调用 align_and_adjust_ohlcv：保证时间轴对齐、停牌补行（OHLC=前收、量=0）。

    仅支持日线（freq="1d"）。
    """

    def __init__(
        self,
        csv_dir: str = "data/zipline_csv",
        calendar_name: str = "XSHG",
        allow_stub: bool = True,
        filename_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        """
        参数：
          csv_dir           : CSV 根目录（默认兼容你之前 Zipline 使用的目录）
          calendar_name     : 交易日历（默认上交所 XSHG）
          allow_stub        : 当找不到 CSV 时，是否生成桩数据（默认为 True）
          filename_patterns : 文件名匹配模式（按顺序尝试），支持 {symbol_base} 与 {symbol_full}
                              - symbol_base：去后缀的代码，如 '002415'
                              - symbol_full：带后缀的内部码，如 '002415.XSHE'
                              默认模式：["{symbol_base}.csv", "{symbol_full}.csv", "{symbol_base}_*.csv"]
        """
        self.csv_dir = os.path.abspath(csv_dir)
        self.calendar_name = calendar_name
        self.allow_stub = bool(allow_stub)
        self.filename_patterns = list(filename_patterns) if filename_patterns else [
            "{symbol_base}.csv",
            "{symbol_full}.csv",
            "{symbol_base}_*.csv",  # 例如形如 002415_2024-*.csv 的切片文件
        ]

    # ----------------------------------------------------------------------
    # 对外主接口
    # ----------------------------------------------------------------------
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
        拉取 OHLCV（标准日线），并按统一规范输出。

        参数：
          symbol  : 内部统一代码（如 002415.XSHE / 600000.XSHG）
          start   : 开始日期（'YYYY-MM-DD'）
          end     : 结束日期（'YYYY-MM-DD'）
          freq    : 目前仅支持 "1d"
          adjust  : "pre"=尽可能按前复权返回；"none"=不复权
          kwargs  : 预留参数（暂未使用）

        返回：
          DataFrame（index=日期，columns=['open','high','low','close','volume']）
        """
        if freq != "1d":
            raise NotImplementedError("CsvProvider 目前仅支持日线 freq='1d'。")

        # 1）寻找 CSV 文件
        csv_path = self._resolve_csv_path(symbol)
        if not csv_path or not os.path.exists(csv_path):
            if not self.allow_stub:
                # 返回结构一致的空表，避免上层崩溃
                return self._empty_frame()
            # 允许 stub：生成区间桩数据
            df_used = self._make_stub_ohlcv(start, end)
            # 直接对齐并返回（stub 数据不做复权）
            return align_and_adjust_ohlcv(
                df_used,
                start=start,
                end=end,
                calendar_name=self.calendar_name,
                adjust="none"
            )

        # 2）读取 CSV 并标准化列
        raw = self._read_csv(csv_path)
        if raw.empty:
            return self._empty_frame()

        df_used, has_factor = self._normalize_columns(raw)

        # 3）处理"前复权"
        # 若 CSV 含有复权因子（adj_factor/factor），则执行：前复权价 = 原价 * (adj_factor / 最新因子)
        # 若没有因子：
        #   - adjust="none"：直接进入对齐流程；
        #   - adjust="pre" ：做最简近似（等价于 none），给出合理的容忍（避免二次复权）。
        if adjust.lower() == "pre" and has_factor:
            latest = float(df_used["adj_factor"].iloc[-1]) if df_used["adj_factor"].iloc[-1] else 1.0
            latest = latest if latest != 0 else 1.0
            ratio = df_used["adj_factor"] / latest
            for col in ["open", "high", "low", "close"]:
                df_used[col] = pd.to_numeric(df_used[col], errors="coerce") * ratio
        # 无因子或 adjust="none"：不做价格变换

        # 4）仅保留标准列，索引为日期
        df_used = df_used[["open", "high", "low", "close", "volume"]].astype(float)

        # 5）统一时间轴对齐 + 停牌补行（由 normalize 模块统一处理）
        # 修复：移除不存在的参数
        df_final = align_and_adjust_ohlcv(
            df_used,
            start=start,
            end=end,
            calendar_name=self.calendar_name,
            adjust="none"  # 此处已按是否含因子处理价格，不再二次复权
        )
        return df_final

    # ----------------------------------------------------------------------
    # 内部工具
    # ----------------------------------------------------------------------
    def _resolve_csv_path(self, symbol: str) -> Optional[str]:
        """
        根据 symbol 生成候选文件名，并在 csv_dir 中查找存在的文件。
        兼容两类符号：
          - 带后缀的内部码：002415.XSHE / 600000.XSHG
          - 去后缀的代码：002415 / 600000
        也兼容 Zipline CSV（如 TEST.csv / 002415.csv 等）。
        """
        s = (symbol or "").upper().strip()
        base = s.split(".", 1)[0]  # 去掉 .XSHE/.XSHG 等后缀
        full = s  # 保留原始

        candidates: list[str] = []
        for pat in self.filename_patterns:
            # 将模式中的占位符替换
            p = pat.format(symbol_base=base, symbol_full=full)
            # 支持通配符的情况，取第一个匹配到的文件
            globbed = sorted(glob.glob(os.path.join(self.csv_dir, p)))
            if globbed:
                candidates.extend(globbed)
            else:
                # 若模式不含通配符，则也拼接一个具体路径作为候选
                if "*" not in p and "?" not in p:
                    candidates.append(os.path.join(self.csv_dir, p))

        # 依次返回第一个真实存在的文件
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        """返回结构一致的空 DataFrame。"""
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], name=None),
        )

    @staticmethod
    def _read_csv(path: str) -> pd.DataFrame:
        """
        读取 CSV（尽量宽松）：
          - 自动识别分隔符（默认逗号）；
          - 不强制指定编码（如出现编码问题可按需修改为 encoding="utf-8"）。
        """
        return pd.read_csv(path)

    @staticmethod
    def _pick_date_col(df: pd.DataFrame) -> Optional[str]:
        """从常见字段中选择"日期列"的列名。"""
        candidates = ["date", "trade_date", "t", "timestamp", "dt"]
        lower_cols = {c.lower(): c for c in df.columns}
        for k in candidates:
            if k in lower_cols:
                return lower_cols[k]
        # 若不存在常见命名，但第 0 列看起来像日期，也可尝试
        return None

    def _normalize_columns(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        """
        统一列名与索引：
          - 识别日期列并设为索引（tz-naive）；
          - 识别 open/high/low/close/volume（兼容大小写与 'vol','v'）；
          - 识别 adj_factor/factor（若存在返回 has_factor=True）。

        返回：
          (标准化后的 DataFrame, has_factor)
        """
        # 1）处理日期列
        date_col = self._pick_date_col(df)
        if date_col is None and "date" not in df.columns:
            # 尝试自动推断：若第一列能转日期，则使用第一列
            first_col = df.columns[0]
            try:
                _ = pd.to_datetime(df[first_col], errors="raise")
                date_col = first_col
            except Exception:
                pass
        if date_col is None:
            # 若仍为空，则创建一个无行的空表
            return self._empty_frame(), False

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        # 设为索引，并保证 tz-naive，升序排列
        df = df.set_index(date_col).sort_index()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # 2）标准列名映射（大小写/别名）
        col_map = {c.lower(): c for c in df.columns}
        def _first(*names: str) -> Optional[str]:
            for n in names:
                if n in col_map:
                    return col_map[n]
            return None

        open_col  = _first("open", "o")
        high_col  = _first("high", "h")
        low_col   = _first("low", "l")
        close_col = _first("close", "c")
        vol_col   = _first("volume", "vol", "v")

        # 若缺少核心列，返回空表
        if not all([open_col, high_col, low_col, close_col]):
            return self._empty_frame(), False

        out = pd.DataFrame(index=df.index.copy())
        out["open"]  = pd.to_numeric(df[open_col], errors="coerce")
        out["high"]  = pd.to_numeric(df[high_col], errors="coerce")
        out["low"]   = pd.to_numeric(df[low_col], errors="coerce")
        out["close"] = pd.to_numeric(df[close_col], errors="coerce")

        if vol_col:
            out["volume"] = pd.to_numeric(df[vol_col], errors="coerce").fillna(0.0)
        else:
            out["volume"] = 0.0  # 若无成交量列，兜底为 0

        # 3）识别复权因子
        factor_col = _first("adj_factor", "factor")
        has_factor = False
        if factor_col and factor_col in df.columns:
            # 确保为 float，缺失用前后值填充（防止少量空洞）
            fac = pd.to_numeric(df[factor_col], errors="coerce")
            fac = fac.ffill().bfill()
            out["adj_factor"] = fac.astype(float)
            has_factor = True

        return out, has_factor

    # ----------------------------------------------------------------------
    # 桩数据（Stub）生成：用于无 CSV 时的兜底
    # ----------------------------------------------------------------------
    def _make_stub_ohlcv(self, start: str, end: str) -> pd.DataFrame:
        """
        生成一段"看起来合理"的桩数据：
          - 价格做轻微趋势与噪声；
          - 高低价在开收价附近波动；
          - 成交量为正随机数。
        """
        # 用对齐函数的会话轴，保证与真实交易日一一对应
        # 这里先造一段 close，再派生出其余列（注意：align_and_adjust_ohlcv 会再做补齐）
        dates = pd.date_range(start=pd.Timestamp(start), end=pd.Timestamp(end), freq="D")
        if len(dates) == 0:
            return self._empty_frame()

        rng = np.random.default_rng(42)
        n = len(dates)
        # 构造一个温和向上的随机游走作为收盘价
        base = 10.0
        steps = rng.normal(loc=0.02, scale=0.05, size=n).cumsum()
        close = base * (1.0 + steps / 10.0).clip(min=0.2)

        # 开盘价为收盘价附近的小幅偏移
        open_ = close * (1 + rng.normal(loc=0.0, scale=0.005, size=n))
        # 高/低在开收价附近波动
        high = np.maximum(open_, close) * (1 + rng.normal(loc=0.001, scale=0.004, size=n).clip(min=-0.002))
        low  = np.minimum(open_, close) * (1 - rng.normal(loc=0.001, scale=0.004, size=n).clip(min=-0.002))
        # 成交量正态取整为正
        volume = (rng.normal(loc=1_000_000, scale=200_000, size=n)).clip(min=10_000)

        df = pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
            index=pd.DatetimeIndex(dates),
        )
        # 确保为 float
        df = df.astype(float)
        return df