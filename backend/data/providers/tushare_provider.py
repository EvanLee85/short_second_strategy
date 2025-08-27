# -*- coding: utf-8 -*-
"""
TuShare 适配器 - 修复版本
----------------
修复内容：
  - 移除align_and_adjust_ohlcv调用中不存在的参数
  - 添加基于tenacity的重试机制
  - 添加请求限流功能
  - 改进错误处理和日志记录
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, Optional

import pandas as pd

from .base import BaseMarketDataProvider
from backend.data.normalize import align_and_adjust_ohlcv
from backend.data.exceptions import (
    ProviderError,
    NetworkError, 
    RateLimitError,
    AuthenticationError,
    ErrorSeverity,
    report_error
)

# 导入重试和限流装饰器
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

# 日志记录器
logger = logging.getLogger(__name__)


class TuShareProvider(BaseMarketDataProvider):
    """
    TuShare 数据提供器 - 增强版
    
    增强功能：
    - 基于tenacity的指数退避重试
    - 请求限流保护
    - 更好的错误分类和处理
    - 详细的操作日志
    """

    def __init__(
        self,
        token: Optional[str] = None,
        calendar_name: str = "XSHG",
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_sleep: float = 1.0,
        enable_retry: bool = True,
        enable_rate_limit: bool = True,
        rate_limit_per_minute: int = 200,  # 每分钟最大请求数
    ) -> None:
        """
        参数：
          token         : TuShare 授权 token；若为 None，则从环境变量 TUSHARE_TOKEN 读取
          calendar_name : 交易日历名称（默认 XSHG）
          timeout       : 访问超时时间（秒）
          max_retries   : 失败重试次数
          retry_sleep   : 基础重试间隔（秒）
          enable_retry  : 是否启用重试功能
          enable_rate_limit : 是否启用限流功能
          rate_limit_per_minute : 每分钟最大请求数
        """
        self.token = token or os.environ.get("TUSHARE_TOKEN", "").strip()
        if not self.token:
            raise RuntimeError(
                "TuShareProvider 初始化失败：未找到 token。"
                "请在构造参数传入 token，或设置环境变量 TUSHARE_TOKEN。"
            )
        
        try:
            import tushare as ts
            self._ts = ts
            self._pro = ts.pro_api(self.token)
        except Exception as e:
            raise ImportError(
                "未安装 tushare，请先 `pip install tushare`。"
            ) from e

        self.calendar_name = calendar_name
        self.timeout = float(timeout)
        self.max_retries = int(max_retries)
        self.retry_sleep = float(retry_sleep)
        self.enable_retry = enable_retry
        self.enable_rate_limit = enable_rate_limit
        
        # 限流控制
        self.rate_limit_per_minute = rate_limit_per_minute
        self._last_requests = []  # 记录最近的请求时间
        
        # 提供器名称
        self.name = "tushare"
        
        logger.info(
            f"TuShareProvider initialized: "
            f"retry={self.enable_retry}({self.max_retries}), "
            f"rate_limit={self.enable_rate_limit}({self.rate_limit_per_minute}/min), "
            f"timeout={self.timeout}s"
        )

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
                logger.warning(f"TuShare rate limit reached, waiting {wait_time:.1f}s")
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
                    for attempt in range(self.max_retries):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            last_exception = e
                            if attempt < self.max_retries - 1:
                                wait_time = self.retry_sleep * (2 ** attempt)  # 指数退避
                                logger.warning(f"TuShare attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                                time.sleep(wait_time)
                    raise last_exception
                return wrapper
            return simple_retry
        
        # 使用tenacity的高级重试
        return retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=self.retry_sleep,
                min=self.retry_sleep,
                max=30.0
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
    def _internal_to_ts_code(symbol: str) -> str:
        """
        将内部统一代码转换为 TuShare ts_code
        002415.XSHE -> 002415.SZ
        600000.XSHG -> 600000.SH
        """
        s = (symbol or "").upper().strip()
        if "." in s:
            code, exch = s.split(".", 1)
            if exch == "XSHE":
                return f"{code}.SZ"
            if exch == "XSHG":
                return f"{code}.SH"
            return s
        # 无后缀：做最小化猜测
        if s.startswith("6"):
            return f"{s}.SH"
        return f"{s}.SZ"

    @staticmethod
    def _yyyymmdd(x: str | pd.Timestamp) -> str:
        """将日期转为YYYYMMDD格式"""
        ts = pd.Timestamp(x)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts.strftime("%Y%m%d")

    def _fetch_with_retry(self, api_func, **kwargs):
        """带重试的API调用"""
        retry_decorator = self._create_retry_decorator()
        
        @retry_decorator
        def _call_api():
            self._check_rate_limit()
            
            try:
                result = api_func(**kwargs)
                if result is None or (hasattr(result, 'empty') and result.empty):
                    raise ProviderError(f"TuShare API returned empty result for {kwargs}")
                return result
            except Exception as e:
                # 分类异常
                error_msg = str(e).lower()
                if "token" in error_msg or "invalid" in error_msg:
                    raise AuthenticationError(f"TuShare authentication failed: {e}", provider=self.name)
                elif "limit" in error_msg or "频繁" in error_msg:
                    raise RateLimitError(f"TuShare rate limit: {e}", provider=self.name, retry_after=60)
                elif "network" in error_msg or "connection" in error_msg:
                    raise NetworkError(f"TuShare network error: {e}", provider=self.name)
                else:
                    raise ProviderError(f"TuShare API error: {e}", provider=self.name, root_cause=e)
        
        return _call_api()

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
        拉取 OHLCV 数据
        """
        if freq != "1d":
            raise NotImplementedError("TuShareProvider 目前仅支持日线 freq='1d'。")

        ts_code = self._internal_to_ts_code(symbol)
        start_yyyymmdd = self._yyyymmdd(start)
        end_yyyymmdd = self._yyyymmdd(end)

        logger.info(f"Fetching TuShare data: {ts_code}, {start_yyyymmdd} to {end_yyyymmdd}")

        # 获取日线数据
        df_daily = self._fetch_with_retry(
            self._pro.daily,
            ts_code=ts_code,
            start_date=start_yyyymmdd,
            end_date=end_yyyymmdd,
        )

        if df_daily is None or df_daily.empty:
            logger.warning(f"No daily data returned for {ts_code}")
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"],
                index=pd.DatetimeIndex([], name=None),
            )

        # 排序（TuShare默认降序）
        df_daily = df_daily.sort_values("trade_date").reset_index(drop=True)

        # 前复权处理
        if adjust.lower() == "pre":
            try:
                df_adj = self._fetch_with_retry(
                    self._pro.adj_factor,
                    ts_code=ts_code,
                    start_date=start_yyyymmdd,
                    end_date=end_yyyymmdd,
                )
                
                if df_adj is not None and not df_adj.empty:
                    df_adj = df_adj.sort_values("trade_date").reset_index(drop=True)
                    dfm = pd.merge(df_daily, df_adj[["trade_date", "adj_factor"]], on="trade_date", how="left")
                    dfm["adj_factor"] = dfm["adj_factor"].ffill().bfill()
                    
                    latest = float(dfm["adj_factor"].iloc[-1]) if not dfm["adj_factor"].empty else 1.0
                    latest = latest if latest != 0 else 1.0
                    ratio = dfm["adj_factor"] / latest

                    # 调整OHLC
                    for col in ["open", "high", "low", "close"]:
                        dfm[col] = pd.to_numeric(dfm[col], errors="coerce") * ratio

                    df_used = dfm.copy()
                    logger.info(f"Applied pre-adjustment for {ts_code}")
                else:
                    df_used = df_daily.copy()
                    logger.warning(f"No adjustment factors found for {ts_code}, using raw prices")
            except Exception as e:
                logger.warning(f"Failed to get adjustment factors for {ts_code}: {e}, using raw prices")
                df_used = df_daily.copy()
        else:
            df_used = df_daily.copy()

        # 数据标准化
        df_used["volume"] = pd.to_numeric(df_used.get("vol", 0), errors="coerce").fillna(0) * 100  # 手转股
        df_used = df_used.rename(columns={
            "open": "open",
            "high": "high", 
            "low": "low",
            "close": "close",
        })

        # 设置索引为日期
        df_used["trade_date"] = pd.to_datetime(df_used["trade_date"], format="%Y%m%d", errors="coerce")
        df_used = df_used.set_index("trade_date").sort_index()
        df_used = df_used[["open", "high", "low", "close", "volume"]].astype(float)

        # 交易日对齐与停牌补行（修复：移除不存在的参数）
        df_final = align_and_adjust_ohlcv(
            df_used,
            start=start,
            end=end,
            calendar_name=self.calendar_name,
            adjust="none"  # 已做复权处理，不再二次复权
        )

        logger.info(f"TuShare fetch completed: {ts_code}, {len(df_final)} rows")
        return df_final