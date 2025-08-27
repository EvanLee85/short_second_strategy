# -*- coding: utf-8 -*-
"""
可插拔行情数据提供器的基础定义（统一接口与返回格式）

约定（强制）：
- 方法签名：
    fetch_ohlcv(symbol, start, end, freq="1d", adjust="pre") -> pandas.DataFrame
- 返回 DataFrame：
    * 行索引：日期/时间（可带或不带时区），升序、唯一
    * 列：["open", "high", "low", "close", "volume"]
    * 类型：数值型（close 列不允许出现 NaN）

实现方可在内部自行处理交易日历对齐，但对外必须保证输出按目标市场的有效交易日/时段对齐。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Protocol, Union, runtime_checkable
import pandas as pd


# -------- 类型别名与常量 --------
DateLike = Union[str, pd.Timestamp, "datetime.date", "datetime.datetime"]
Adjust = Literal["none", "pre", "post"]  # 复权方式：不复权/前复权/后复权
Freq = Literal["1d", "1h", "1m"]         # 频率：日/小时/分钟

REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")

__all__ = [
    "DateLike",
    "Adjust",
    "Freq",
    "FetchRequest",
    "ProviderError",
    "DataProvider",
    "BaseMarketDataProvider", 
    "SupportsFetchOHLCV",
    "REQUIRED_COLUMNS",
]


# -------- 统一异常类型 --------
class ProviderError(Exception):
    """当提供器抓取失败或返回数据格式不符合约定时抛出。"""
    pass


# -------- 请求参数模型（可选便捷封装） --------
@dataclass(frozen=True)
class FetchRequest:
    """历史 OHLCV 拉取请求的不可变参数对象。"""
    symbol: str
    start: DateLike
    end: DateLike
    freq: Freq = "1d"
    adjust: Adjust = "pre"


# -------- 抽象基类：所有数据源适配器需实现 --------
class DataProvider(ABC):
    """数据提供器抽象基类。"""

    name: str = "base"  # 实现方可覆盖为自身名称

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        start: DateLike,
        end: DateLike,
        freq: Freq = "1d",
        adjust: Adjust = "pre",
    ) -> pd.DataFrame:
        """
        拉取历史 OHLCV。

        实现方必须遵守：
        - 返回含列：open, high, low, close, volume 的 DataFrame
        - 索引为日期时间，升序且唯一
        - 各数值列需转为数值类型；close 列不得为 NaN
        - 输出需与目标市场交易日/时段一致（不应出现重复/无效会话）

        失败时：
            抛出 ProviderError（包括网络/格式/日历异常等）。
        """
        raise NotImplementedError

    def ping(self) -> bool:
        """可选：轻量健康检查。默认返回 True。"""
        return True

    # ---------- 公共校验与规范化 ----------
    @staticmethod
    def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
        """
        校验并规范化 OHLCV 表结构：
        - 校验必需列
        - 索引转为 datetime、排序、去重
        - 数值列统一转数值
        - close 不允许 NaN
        """
        if not isinstance(df, pd.DataFrame):
            raise ProviderError("fetch_ohlcv 必须返回 pandas.DataFrame")

        # 1) 必需列检查
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ProviderError(f"缺少列：{missing}；实际列={list(df.columns)}")

        # 2) 索引转为日期时间
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            try:
                df = df.copy()
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                raise ProviderError(f"索引必须可转换为 datetime：{e!r}")

        # 3) 排序与去重
        df = df.sort_index()
        if df.index.has_duplicates:
            df = df[~df.index.duplicated(keep="last")]

        # 4) 数值化各列
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # 5) close 不允许 NaN（关键列）
        if df["close"].isna().any():
            bad = df[df["close"].isna()].index[:5].tolist()
            raise ProviderError(f"close 列存在 NaN；示例索引={bad}")

        return df


# -------- 协议：便于做鸭子类型检查（可选） --------
@runtime_checkable
class SupportsFetchOHLCV(Protocol):
    """只要求实现 fetch_ohlcv 的协议类型，便于灵活注入。"""
    def fetch_ohlcv(
        self,
        symbol: str,
        start: DateLike,
        end: DateLike,
        freq: Freq = "1d",
        adjust: Adjust = "pre",
    ) -> pd.DataFrame:
        ...

# 在 base.py 的末尾添加：
BaseMarketDataProvider = DataProvider  # 兼容性别名