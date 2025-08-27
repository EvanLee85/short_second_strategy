# -*- coding: utf-8 -*-
"""
AkShare 数据提供器 - 增强版
=================
增强功能：
  - 基于tenacity的指数退避重试
  - 请求限流保护  
  - 更好的错误分类和处理
  - 详细的操作日志和统计
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Optional, Literal

import pandas as pd

from .base import BaseMarketDataProvider
from backend.data.normalize import (
    to_internal,
    align_and_adjust_ohlcv,
)
from backend.data.exceptions import (
    ProviderError,
    NetworkError,
    RateLimitError,
    ErrorSeverity,
    report_error
)

# 导入重试功能
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
        after_log
    )
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False

# 类型标注
FreqT = Literal["1d"]
AdjustT = Literal["pre", "post", "none"]

# 日志记录器
logger = logging.getLogger(__name__)


@dataclass  
class AkshareProvider(BaseMarketDataProvider):
    """
    AkShare 数据源适配器 - 增强版

    新增参数：
      enable_retry  : 是否启用重试功能（默认True）
      enable_rate_limit : 是否启用限流功能（默认True）
      rate_limit_per_minute : 每分钟最大请求数（默认120）
      min_retry_wait : 最小重试等待时间（秒）
      max_retry_wait : 最大重试等待时间（秒）
    """
    calendar_name: str = "XSHG"
    timeout: float = 15.0
    retries: int = 3  # 向后兼容
    retry_sleep: float = 1.0  # 向后兼容
    default_exchange: str = "XSHE"
    volume_unit: Literal["hands", "shares"] = "hands"
    enable_retry: bool = True
    enable_rate_limit: bool = True
    rate_limit_per_minute: int = 120  # AkShare相对宽松
    min_retry_wait: float = 1.0
    max_retry_wait: float = 30.0

    # 提供器名称
    name: str = "akshare"

    # AkShare 接口复权口径映射
    _AK_ADJUST_MAP = {
        "pre": "qfq",   # 前复权
        "post": "hfq",  # 后复权  
        "none": "",     # 不复权
    }

    def __post_init__(self):
        """初始化后处理"""
        # 限流控制
        self._last_requests = []  # 记录最近的请求时间
        
        logger.info(
            f"AkshareProvider initialized: "
            f"retry={self.enable_retry}({self.retries}), "
            f"rate_limit={self.enable_rate_limit}({self.rate_limit_per_minute}/min), "
            f"timeout={self.timeout}s"
        )

    def _ak_import(self):
        """延迟导入 akshare"""
        try:
            import akshare as ak
            return ak
        except Exception as e:
            error = ProviderError(
                "未能导入 akshare，请先安装：pip install akshare",
                provider=self.name,
                root_cause=e,
                severity=ErrorSeverity.CRITICAL
            )
            report_error(error)
            raise error

    def _check_rate_limit(self):
        """检查并执行限流"""
        if not self.enable_rate_limit:
            return
            
        now = time.time()
        # 清除1分钟前的记录
        self._last_requests = [t for t in self._last_requests if now - t < 60]
        
        # 检查是否超过限流
        if len(self._last_requests) >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self._last_requests[0])
            if wait_time > 0:
                logger.warning(f"AkShare rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                # 重新清理列表
                now = time.time()
                self._last_requests = [t for t in self._last_requests if now - t < 60]
        
        # 记录本次请求
        self._last_requests.append(now)

    def _create_retry_decorator(self):
        """创建重试装饰器"""
        if not HAS_TENACITY or not self.enable_retry:
            # 简单重试实现
            def simple_retry(func):
                def wrapper(*args, **kwargs):
                    last_exception = None
                    for attempt in range(max(1, self.retries)):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            last_exception = e
                            if attempt < self.retries - 1:
                                wait_time = self.retry_sleep * (2 ** attempt)  # 指数退避
                                logger.warning(f"AkShare attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                                time.sleep(wait_time)
                    raise last_exception
                return wrapper
            return simple_retry
        
        # 使用tenacity的高级重试
        return retry(
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(
                multiplier=self.retry_sleep,
                min=self.min_retry_wait,
                max=self.max_retry_wait
            ),
            retry=retry_if_exception_type((
                ConnectionError,
                TimeoutError,
                NetworkError,
                RateLimitError,
            )),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )

    @staticmethod
    def _date_to_ak(s: str | pd.Timestamp) -> str:
        """将日期转换为 AkShare 的 YYYYMMDD 格式"""
        ts = pd.Timestamp(s)
        return ts.strftime("%Y%m%d")

    def _fetch_daily_core_impl(
        self,
        symbol_internal: str,
        start: str,
        end: str,
        adjust: AdjustT,
    ) -> pd.DataFrame:
        """
        核心抓取函数的实现（不含重试装饰器）
        """
        ak = self._ak_import()
        code6 = symbol_internal.split(".")[0]  # 002415.XSHE -> 002415

        start_ = self._date_to_ak(start)
        end_ = self._date_to_ak(end)
        adj = self._AK_ADJUST_MAP.get(adjust, "")

        # 执行限流检查
        self._check_rate_limit()
        
        request_start = time.time()
        logger.debug(f"Fetching AkShare data: {code6}, {start_} to {end_}, adjust={adj}")
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=code6,
                period="daily",
                start_date=start_,
                end_date=end_,
                adjust=adj,
            )
            
            request_duration = time.time() - request_start
            
            if isinstance(df, pd.DataFrame) and not df.empty:
                logger.info(
                    f"AkShare fetch success: {code6}, "
                    f"{len(df)} rows, {request_duration:.2f}s"
                )
                return df
            else:
                raise ProviderError(
                    f"AkShare 返回空数据: symbol={symbol_internal}",
                    provider=self.name,
                    symbol=symbol_internal,
                    severity=ErrorSeverity.MEDIUM
                )
                
        except Exception as e:
            # 将异常分类并转换
            error_msg = str(e).lower()
            if "网络" in error_msg or "timeout" in error_msg or "connection" in error_msg:
                raise NetworkError(
                    f"AkShare 网络请求失败: {e}",
                    provider=self.name,
                    symbol=symbol_internal,
                    root_cause=e
                )
            elif "限流" in error_msg or "rate limit" in error_msg or "频繁" in error_msg:
                raise RateLimitError(
                    f"AkShare 请求限流: {e}",
                    provider=self.name,
                    symbol=symbol_internal,
                    root_cause=e,
                    retry_after=60
                )
            else:
                raise ProviderError(
                    f"AkShare 请求失败: {e}",
                    provider=self.name,
                    symbol=symbol_internal,
                    root_cause=e,
                    severity=ErrorSeverity.HIGH
                )

    def _fetch_daily_core(
        self,
        symbol_internal: str,
        start: str,
        end: str,
        adjust: AdjustT,
    ) -> pd.DataFrame:
        """
        带重试的核心抓取函数
        """
        retry_decorator = self._create_retry_decorator()
        decorated_func = retry_decorator(self._fetch_daily_core_impl)
        return decorated_func(symbol_internal, start, end, adjust)

    @staticmethod
    def _rename_and_scale(df_raw: pd.DataFrame, volume_unit: str) -> pd.DataFrame:
        """
        列名重命名与成交量量纲统一
        """
        colmap = {
            "日期": "date",
            "开盘": "open", 
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }

        # 保留需要的列并重命名
        cols = {k: v for k, v in colmap.items() if k in df_raw.columns}
        if not cols:
            raise ProviderError(
                f"AkShare 返回数据缺少必要列，实际列名: {list(df_raw.columns)}"
            )
            
        df = df_raw[list(cols.keys())].rename(columns=cols).copy()

        # 类型转换
        for c in ("open", "high", "low", "close", "volume"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # 成交量量纲统一
        if "volume" in df.columns:
            if volume_unit == "hands":
                df["volume"] = df["volume"] * 100.0  # 手 -> 股

        # 索引设置为日期
        if "date" not in df.columns:
            raise ProviderError("AkShare 返回缺少日期列")
            
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date").sort_index()

        # 去重同日（保险）
        if df.index.has_duplicates:
            df = df.groupby(df.index).agg({
                "open": "first", "high": "max", "low": "min", 
                "close": "last", "volume": "sum"
            })

        return df[["open", "high", "low", "close", "volume"]]

    def fetch_ohlcv(
        self,
        symbol: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
        freq: FreqT = "1d", 
        adjust: AdjustT = "pre",
    ) -> pd.DataFrame:
        """
        拉取日线 OHLCV 数据
        """
        if freq != "1d":
            raise NotImplementedError("AkshareProvider 当前仅支持日线 freq='1d'")

        # 统一内部代码
        internal = to_internal(symbol, default_exchange=self.default_exchange)

        # 原始抓取（按目标复权口径）
        raw = self._fetch_daily_core(internal, str(start), str(end), adjust=adjust)

        # 列名与量纲统一
        std = self._rename_and_scale(raw, volume_unit=self.volume_unit)

        # 交易日历对齐 + 停牌补行（已复权则不再复权）
        df_final = align_and_adjust_ohlcv(
            std,
            start=str(start),
            end=str(end),
            calendar_name=self.calendar_name,
            adjust="none"  # 避免二次复权
        )

        logger.info(f"AkShare fetch completed: {internal}, {len(df_final)} rows")
        return df_final