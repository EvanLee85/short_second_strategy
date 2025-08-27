# -*- coding: utf-8 -*-
"""
统一数据入口（fetcher）
---------------------------------
用途：
  - 上层仅依赖本模块，不直接依赖具体 Provider
  - 读取配置 → 按优先级逐源拉数 → 规范化/合并 → 缓存 → 返回
  - 面向后端服务与回测的公共 API

核心接口：
  - DataFetcher.get_ohlcv(symbol, start, end, freq="1d", adjust="pre") -> pd.DataFrame
  - DataFetcher.write_zipline_csv(symbols, start, end, out_dir, ...) -> None
  - get_default_fetcher(config_path: Optional[str]) -> DataFetcher
"""

from __future__ import annotations

import os
import time
import logging
import logging.config
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any

import yaml
import pandas as pd

# ---- 日志配置 ----
def setup_logging() -> None:
    """加载/初始化日志配置（若无配置则使用基础配置）。"""
    cfg_path = Path("config/logging.yaml")
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        Path("logs").mkdir(exist_ok=True)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

# 模块导入时初始化日志
setup_logging()

# ---- 引用数据层组件 ----
from backend.data.providers.akshare_provider import AkshareProvider
from backend.data.providers.tushare_provider import TuShareProvider
from backend.data.providers.csv_provider import CsvProvider
from backend.data.merge import merge_ohlcv
from backend.data.cache import cache_ohlcv_get, cache_ohlcv_put
from backend.data.normalize import to_internal

# 异常/错误上报
from backend.data.exceptions import (
    DataSourceError, ErrorContext, ErrorSeverity,
    create_provider_error, report_error, get_global_error_summary
)


@dataclass
class FetchConfig:
    """数据获取配置（可由 YAML 加载）。"""
    # 提供商优先级（越靠前越优先）
    provider_priority: List[str] = field(default_factory=lambda: ["akshare", "tushare", "csv"])
    # 各提供商定制参数
    provider_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 缓存配置
    enable_cache: bool = True
    cache_ttl_hours: Dict[str, int] = field(default_factory=lambda: {"1d": 1, "1h": 0.25, "1m": 0.1})

    # 合并配置
    conflict_threshold: float = 0.02            # 同日收盘价差>2% 记为冲突
    freshness_tolerance_days: int = 3           # 新鲜度容忍天数（主源缺尾时允许回退）

    # 默认口径
    default_calendar: str = "XSHG"              # 上交所交易日历
    default_exchange: str = "XSHE"              # 未带交易所后缀时默认补深交所

    @classmethod
    def from_yaml(cls, config_path: str) -> "FetchConfig":
        """从 YAML 文件加载配置；不存在时使用默认。"""
        if not os.path.exists(config_path):
            logging.getLogger(__name__).warning(f"配置文件不存在: {config_path}，使用默认配置")
            return cls()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(
                provider_priority=data.get("provider_priority", cls().provider_priority),
                provider_configs=data.get("provider_configs", {}),
                enable_cache=data.get("enable_cache", True),
                cache_ttl_hours=data.get("cache_ttl_hours", cls().cache_ttl_hours),
                conflict_threshold=data.get("conflict_threshold", 0.02),
                freshness_tolerance_days=data.get("freshness_tolerance_days", 3),
                default_calendar=data.get("default_calendar", "XSHG"),
                default_exchange=data.get("default_exchange", "XSHE"),
            )
        except Exception as e:
            logging.getLogger(__name__).warning(f"加载配置失败: {e}，使用默认配置")
            return cls()


class DataFetcher:
    """
    统一数据获取器
    职责：
      1) 管理多个数据提供商
      2) 按优先级获取 → 合并冲突 → 产出标准 OHLCV
      3) 读写缓存
      4) 记录数据质量与合并统计
    """

    def __init__(self, config: Optional[FetchConfig] = None) -> None:
        self.config = config or FetchConfig()
        self.logger = logging.getLogger("backend.data.fetcher")
        self.error_logger = logging.getLogger("backend.data.fetcher.errors")
        self.providers = self._init_providers()
        self.session_stats: Dict[str, Any] = {}
        self.logger.info(f"已初始化提供商: {list(self.providers.keys())}")

    # ---------- 私有工具 ----------

    def _init_providers(self) -> Dict[str, Any]:
        """按优先级初始化各 Provider 实例。"""
        providers: Dict[str, Any] = {}
        for name in self.config.provider_priority:
            try:
                cfg = self.config.provider_configs.get(name, {})
                if name == "akshare":
                    providers[name] = AkshareProvider(
                        calendar_name=self.config.default_calendar,
                        default_exchange=self.config.default_exchange,
                        **cfg
                    )
                elif name == "tushare":
                    providers[name] = TuShareProvider(
                        calendar_name=self.config.default_calendar,
                        **cfg
                    )
                elif name == "csv":
                    providers[name] = CsvProvider(
                        calendar_name=self.config.default_calendar,
                        **cfg
                    )
                else:
                    self.logger.warning(f"未知提供商: {name}（忽略）")
            except Exception as e:
                self.logger.warning(f"初始化提供商失败: {name} -> {e}")
        return providers

    def _get_cache_ttl(self, freq: str) -> int:
        """按频率返回缓存 TTL（单位：小时）。"""
        return int(self.config.cache_ttl_hours.get(freq, 1))

    def _fetch_from_provider(
        self,
        provider_name: str,
        symbol: str,
        start: str,
        end: str,
        freq: str,
        adjust: str
    ) -> Optional[pd.DataFrame]:
        """向指定提供商拉取数据（带日志与错误上报）。"""
        if provider_name not in self.providers:
            return None

        t0 = time.time()
        context = ErrorContext(
            provider=provider_name, symbol=symbol,
            start_date=start, end_date=end,
            freq=freq, adjust=adjust, operation="fetch"
        )

        try:
            provider = self.providers[provider_name]
            df = provider.fetch_ohlcv(symbol, start, end, freq, adjust)
            context.duration_ms = (time.time() - t0) * 1000.0

            if df is not None and not df.empty:
                context.returned_sessions = len(df)
                self.logger.info(
                    f"数据获取成功 | {provider_name} | {symbol} | "
                    f"{len(df)} 行 | {context.duration_ms:.1f}ms"
                )
                self._log_data_quality(df, context)
                return df
            else:
                self.logger.warning(f"数据源返回空结果 | {provider_name} | {symbol}")
                return None

        except Exception as e:
            context.duration_ms = (time.time() - t0) * 1000.0
            error = create_provider_error(
                provider=provider_name, symbol=symbol, operation="fetch",
                error=e, context=context
            )
            report_error(error)
            self.error_logger.error(
                f"数据获取失败 | {provider_name} | {symbol} | "
                f"错误: {e} | {context.duration_ms:.1f}ms"
            )
            return None

    def _log_data_quality(self, df: pd.DataFrame, context: ErrorContext) -> None:
        """记录单源数据质量（空值/异常 OHLC/极端波动等）。"""
        try:
            total = len(df)
            null_close = int(df["close"].isna().sum())
            null_volume = int(df["volume"].isna().sum())
            zero_volume = int((df["volume"] == 0).sum())
            invalid_ohlc = int(((df["high"] < df["low"]) |
                                (df["close"] < df["low"]) |
                                (df["close"] > df["high"])).sum())
            extreme_moves = 0
            if total > 1:
                extreme_moves = int(df["close"].pct_change().abs().gt(0.20).sum())

            if null_close or invalid_ohlc or extreme_moves:
                self.logger.warning(
                    "数据质量问题 | %s | %s | 空收盘=%d 无量=%d 零量=%d 无效OHLC=%d 极端变动=%d",
                    context.provider, context.symbol,
                    null_close, null_volume, zero_volume, invalid_ohlc, extreme_moves
                )
        except Exception as e:
            self.logger.warning(f"数据质量检查失败: {e}")

    def _log_merge_results(self, merged_df: pd.DataFrame, merge_logs: dict, symbol: str) -> None:
        """记录合并后的统计（冲突/回填/主源/覆盖率等）。"""
        try:
            conflicts = merge_logs.get("conflicts", [])
            fallback_used = int(merge_logs.get("fallback_used", 0))
            primary_source = merge_logs.get("primary")
            providers_quality = merge_logs.get("providers_quality", [])

            total_sessions = 0 if merged_df is None or merged_df.empty else len(merged_df)
            source_coverage = {
                q.get("name"): q.get("coverage", 0.0) for q in providers_quality
            }

            merge_summary = {
                "symbol": symbol,
                "total_sessions": total_sessions,
                "primary_source": primary_source,
                "source_coverage": source_coverage,
                "conflicts": len(conflicts),
                "fallback_sessions": fallback_used,
                "data_completeness": (
                    sum(source_coverage.values()) / max(1, len(source_coverage))
                ),
            }

            has_issues = bool(conflicts) or (fallback_used > 0)
            if has_issues:
                self.logger.warning(
                    "数据合并完成(有问题) | %s | 主源=%s 冲突=%d 回填=%d 覆盖率=%s",
                    symbol, primary_source, len(conflicts), fallback_used, source_coverage
                )
                if conflicts:
                    for c in conflicts[:3]:
                        self.logger.warning(
                            "数据冲突 | %s | %s | %s:%.4f vs %s:%.4f | 决策=%s",
                            symbol, c.get("date"),
                            c.get("primary"), c.get("primary_val", float("nan")),
                            c.get("alt"), c.get("alt_val", float("nan")),
                            c.get("decision")
                        )
                    if len(conflicts) > 3:
                        self.logger.warning("... 还有 %d 个冲突未展开", len(conflicts) - 3)
            else:
                self.logger.info(
                    "数据合并完成(无问题) | %s | 主源=%s | 总计 %d 天 | 覆盖率=%s",
                    symbol, primary_source, total_sessions, source_coverage
                )

            self.session_stats[symbol] = merge_summary
        except Exception as e:
            self.logger.warning(f"合并结果记录失败: {e}")

    # ---------- 对外主流程 ----------

    def get_ohlcv(
        self,
        symbol: str,
        start: str,
        end: str,
        freq: str = "1d",
        adjust: str = "pre"
    ) -> pd.DataFrame:
        """
        获取标准 OHLCV（按配置多源拉取+合并+缓存）。
        返回：
          - 索引：DatetimeIndex（tz-naive、交易日）
          - 列：open, high, low, close, volume
        """
        t_start = time.time()

        # 1) 代码标准化
        try:
            internal_symbol = to_internal(symbol, default_exchange=self.config.default_exchange)
            self.logger.debug("代码标准化: %s -> %s", symbol, internal_symbol)
        except Exception as e:
            err = DataSourceError(
                f"Symbol standardization failed: {symbol}",
                symbol=symbol, operation="standardize",
                root_cause=e, severity=ErrorSeverity.HIGH
            )
            report_error(err)
            self.error_logger.error("代码标准化失败: %s -> %s", symbol, e)
            raise err

        # 2) 缓存读取
        if self.config.enable_cache:
            ttl = self._get_cache_ttl(freq)
            for name in self.config.provider_priority:
                try:
                    cached = cache_ohlcv_get(internal_symbol, start, end, freq, name, ttl)
                    if cached is not None:
                        dur = (time.time() - t_start) * 1000.0
                        self.logger.info(
                            "缓存命中 | %s | %s | %d 行 | %.1fms",
                            name, internal_symbol, len(cached), dur
                        )
                        return cached
                except Exception as e:
                    self.logger.warning("缓存读取异常: %s/%s -> %s", name, internal_symbol, e)

        # 3) 逐源拉取
        provider_data: Dict[str, pd.DataFrame] = {}
        provider_errors: Dict[str, str] = {}
        for name in self.config.provider_priority:
            try:
                df = self._fetch_from_provider(name, internal_symbol, start, end, freq, adjust)
                if df is not None and not df.empty:
                    provider_data[name] = df
                else:
                    self.logger.debug("提供商返回空: %s", name)
            except Exception as e:
                provider_errors[name] = str(e)
                self.logger.warning("提供商异常: %s -> %s", name, e)

        self.logger.info(
            "提供商获取完成 | %s | 成功: %s | 失败: %s",
            internal_symbol, list(provider_data.keys()), list(provider_errors.keys())
        )

        if not provider_data:
            # 所有数据源失败：返回结构正确的空 DataFrame
            err_msg = f"所有数据源均失败: {internal_symbol}"
            report_error(DataSourceError(
                err_msg, symbol=internal_symbol, start_date=start, end_date=end,
                operation="fetch_all", severity=ErrorSeverity.CRITICAL,
                context=ErrorContext(symbol=internal_symbol, start_date=start, end_date=end, operation="fetch_all")
            ))
            self.error_logger.error("%s | 详情: %s", err_msg, provider_errors)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"]).astype(float)

        # 4) 合并
        if len(provider_data) == 1:
            merged_df = next(iter(provider_data.values()))
            primary = next(iter(provider_data.keys()))
            merge_logs = {
                "primary": primary, "conflicts": [], "fallback_used": 0,
                "providers_quality": [{"name": primary, "coverage": 1.0, "score": 100.0}]
            }
            self.logger.info("单源数据 | %s | %s | %d 行", primary, internal_symbol, len(merged_df))
        else:
            self.logger.info("多源合并开始 | %s | 源: %s", internal_symbol, list(provider_data.keys()))
            try:
                merged_df, merge_logs = merge_ohlcv(
                    provider_data,
                    start=start, end=end, calendar_name=self.config.default_calendar,
                    prefer_order=self.config.provider_priority,
                    conflict_close_pct=self.config.conflict_threshold,
                    freshness_tolerance_days=self.config.freshness_tolerance_days
                )
            except Exception as e:
                merge_err = DataSourceError(
                    f"Data merge failed: {internal_symbol}",
                    symbol=internal_symbol, start_date=start, end_date=end,
                    operation="merge", root_cause=e, severity=ErrorSeverity.HIGH
                )
                report_error(merge_err)
                self.error_logger.error("合并失败: %s -> %s", internal_symbol, e)
                raise merge_err

        self._log_merge_results(merged_df, merge_logs, internal_symbol)

        # 5) 写缓存
        if self.config.enable_cache and merged_df is not None and not merged_df.empty:
            try:
                primary = merge_logs.get("primary", self.config.provider_priority[0])
                cache_ohlcv_put(merged_df, internal_symbol, start, end, freq, primary)
                self.logger.debug("数据已缓存: %s/%s", primary, internal_symbol)
            except Exception as e:
                self.logger.warning("缓存写入失败: %s", e)

        # 6) 总结日志
        total_ms = (time.time() - t_start) * 1000.0
        self.logger.info(
            "数据获取完成 | %s | %d 行 | 主源=%s | 总耗时=%.1fms",
            internal_symbol, 0 if merged_df is None else len(merged_df),
            merge_logs.get("primary"), total_ms
        )
        return merged_df

    def write_zipline_csv(
        self,
        symbols: Union[str, List[str]],
        start: str,
        end: str,
        out_dir: str,
        freq: str = "1d",
        adjust: str = "pre"
    ) -> None:
        """
        批量写 Zipline CSV（列：date,open,high,low,close,volume）。
        注：此函数仅做落盘，不做 ingest。
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        self.logger.info("开始生成 Zipline CSV: %d 只股票 -> %s", len(symbols), out_dir)
        for sym in symbols:
            try:
                df = self.get_ohlcv(sym, start, end, freq, adjust)
                if df is None or df.empty:
                    self.logger.warning("跳过空数据: %s", sym)
                    continue

                zdf = df.reset_index().rename(columns={"index": "date"})
                zdf["date"] = pd.to_datetime(zdf["date"]).dt.strftime("%Y-%m-%d")
                zdf = zdf[["date", "open", "high", "low", "close", "volume"]]

                internal = to_internal(sym, default_exchange=self.config.default_exchange)
                clean = internal.split(".")[0]  # 仅文件名使用纯代码
                fp = out_path / f"{clean}.csv"
                zdf.to_csv(fp, index=False)
                self.logger.info("已写入: %s (%d 行)", fp, len(zdf))
            except Exception as e:
                self.logger.error("处理 %s 时出错: %s", sym, e)
        self.logger.info("Zipline CSV 生成完成: %s", out_dir)

    # ---------- 统计与收尾 ----------

    def get_session_statistics(self) -> dict:
        """返回本次会话的数据统计摘要。"""
        return {
            "total_requests": len(self.session_stats),
            "stats_by_symbol": self.session_stats,
            "global_error_summary": get_global_error_summary()
        }

    def log_session_summary(self) -> None:
        """将会话统计打印到日志。"""
        stats = self.get_session_statistics()
        if stats["total_requests"] <= 0:
            return

        self.logger.info("会话统计 | 总请求: %d 个标的", stats["total_requests"])
        source_usage: Dict[str, int] = {}
        total_conflicts = 0
        total_fallbacks = 0

        for _, s in stats["stats_by_symbol"].items():
            primary = s.get("primary_source")
            if primary:
                source_usage[primary] = source_usage.get(primary, 0) + 1
            total_conflicts += int(s.get("conflicts", 0))
            total_fallbacks += int(s.get("fallback_sessions", 0))

        self.logger.info(
            "会话汇总 | 主源使用: %s | 总冲突: %d 天 | 总回填: %d 天",
            source_usage, total_conflicts, total_fallbacks
        )

    def __del__(self) -> None:
        """析构时尝试打印一次会话统计（忽略异常避免进程退出噪音）。"""
        try:
            self.log_session_summary()
        except Exception:
            pass


# ---- 单例获取器与便捷函数 ----

_default_fetcher: Optional[DataFetcher] = None

def get_default_fetcher(config_path: Optional[str] = None) -> DataFetcher:
    """获取/创建默认 DataFetcher 单例实例。"""
    global _default_fetcher
    if _default_fetcher is None:
        if config_path and os.path.exists(config_path):
            cfg = FetchConfig.from_yaml(config_path)
        else:
            default_cfg = "config/data_providers.yaml"
            cfg = FetchConfig.from_yaml(default_cfg) if os.path.exists(default_cfg) else FetchConfig()
        _default_fetcher = DataFetcher(cfg)
    return _default_fetcher


# 示例配置模板（可打印到控制台帮助落盘）
EXAMPLE_CONFIG_YAML = """
# 保存为: config/data_providers.yaml
provider_priority:
  - akshare
  - tushare
  - csv

provider_configs:
  akshare:
    timeout: 15.0
    retries: 3
    volume_unit: hands   # 'hands' 或 'shares'
  tushare:
    timeout: 10.0
    max_retries: 2       # token 从环境变量 TUSHARE_TOKEN 读取
  csv:
    csv_dir: "data/zipline_csv"
    allow_stub: true

enable_cache: true
cache_ttl_hours:
  1d: 1
  1h: 0.25
  1m: 0.1

conflict_threshold: 0.02
freshness_tolerance_days: 3

default_calendar: "XSHG"
default_exchange: "XSHE"
"""
