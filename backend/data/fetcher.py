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

模块级便捷函数（兼容旧代码 / MacroFilter 依赖）：
  - get_ohlcv(...): 调用默认 DataFetcher
  - get_vix() / get_global_futures_change() / get_index_above_ma(...) /
    get_market_breadth() / get_northbound_score() 等：提供可运行的安全兜底
"""

from __future__ import annotations

import os, random, math
import time, datetime
import json
import logging
import logging.config
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Iterable
from datetime import timedelta
from datetime import datetime as dt

import yaml
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None

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
logger = logging.getLogger("data.fetcher")

# ---- 引用数据层组件 ----
from backend.data.providers.akshare_provider import AkshareProvider
from backend.data.providers.tushare_provider import TuShareProvider
from backend.data.providers.csv_provider import CsvProvider

from backend.data.merge import merge_ohlcv
from backend.data.cache import cache_ohlcv_get, cache_ohlcv_put
from backend.data.normalize import to_internal, get_sessions_index

# 异常/错误上报（第12步）
from backend.data.exceptions import (
    DataSourceError, ErrorContext, ErrorSeverity,
    create_provider_error, report_error, get_global_error_summary
)

# 技术指标（用于 get_index_above_ma 的计算）
try:
    from backend.analysis.technical import ma
except Exception:
    # 兜底：简单均线
    def ma(s: pd.Series, n: int) -> pd.Series:
        return pd.Series(s).rolling(n, min_periods=1).mean()


# =========================
# 配置对象
# =========================
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
    def from_yaml(cls, config_path: str | Path) -> "FetchConfig":
        """从 YAML 加载配置，不存在则使用默认。"""
        p = Path(config_path)
        if not p.exists():
            logger.warning("未找到数据提供商配置 %s，使用默认值。", p)
            return cls()
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            return cls(
                provider_priority=data.get("provider_priority", cls().provider_priority),
                provider_configs=data.get("provider_configs", {}),
                enable_cache=data.get("enable_cache", True),
                cache_ttl_hours=data.get("cache_ttl_hours", cls().cache_ttl_hours),
                conflict_threshold=float(data.get("conflict_threshold", 0.02)),
                freshness_tolerance_days=int(data.get("freshness_tolerance_days", 3)),
                default_calendar=data.get("default_calendar", "XSHG"),
                default_exchange=data.get("default_exchange", "XSHE"),
            )
        except Exception as e:
            logger.exception("解析 %s 失败，使用默认配置。err=%s", p, e)
            return cls()


# =========================
# DataFetcher 主体
# =========================
class DataFetcher:
    """统一数据读取器：按优先级尝试各 Provider，做统一规范化、合并与缓存。"""

    def __init__(self, config: Optional[FetchConfig] = None):
        self.cfg = config or FetchConfig.from_yaml("config/data_providers.yaml")
        self.providers: Dict[str, Any] = {}
        self._init_providers()
        logger.info("DataFetcher 初始化完毕：providers=%s", list(self.providers.keys()))

    def _init_providers(self) -> None:
        """按配置初始化各 Provider 实例。"""
        pcfgs = self.cfg.provider_configs or {}

        # AkShare
        self.providers["akshare"] = AkshareProvider(
            calendar_name=self.cfg.default_calendar,
            **(pcfgs.get("akshare", {}) or {})
        )
        # TuShare
        self.providers["tushare"] = TuShareProvider(
            calendar_name=self.cfg.default_calendar,
            **(pcfgs.get("tushare", {}) or {})
        )
        # CSV / 本地桩
        self.providers["csv"] = CsvProvider(
            calendar_name=self.cfg.default_calendar,
            **(pcfgs.get("csv", {}) or {})
        )

    # ---------- 内部工具 ----------
    def _normalize_symbol(self, symbol: str) -> str:
        """统一内部代码形态（如 002415.XSHE）。"""
        return to_internal(symbol, default_exchange=self.cfg.default_exchange)

    def _cache_key(self, provider: str, symbol: str, start: str, end: str,
                   freq: str, adjust: str) -> str:
        return f"{provider}:{symbol}:{start}:{end}:{freq}:{adjust}"

    def _log_data_quality(self, merged_df: pd.DataFrame, by_provider_rows: Dict[str, int]) -> None:
        """记录合并结果的质量信息（缺失补行数、各来源占比等）。"""
        try:
            total = int(merged_df.shape[0])
            src_pct = {k: (v / total if total else 0.0) for k, v in by_provider_rows.items()}
            info = {
                "rows": total,
                "sources_rows": by_provider_rows,
                "sources_pct": {k: round(p, 4) for k, p in src_pct.items()}
            }
            logger.info("合并数据质量: %s", json.dumps(info, ensure_ascii=False))
        except Exception:
            logger.debug("记录数据质量信息失败。")

    def _log_merge_results(self, merged_df: pd.DataFrame, meta: Dict[str, Any]) -> None:
        """记录合并过程元信息（冲突天数、补行数等）。"""
        try:
            logger.info("合并结果: rows=%s meta=%s", merged_df.shape[0], json.dumps(meta, ensure_ascii=False))
        except Exception:
            logger.debug("记录合并元信息失败。")

    # ---------- 核心能力：按优先级拉取并合并 ----------
    def get_ohlcv(self,
                  symbol: str,
                  start: str,
                  end: str,
                  freq: str = "1d",
                  adjust: str = "pre") -> pd.DataFrame:
        """
        读取 K 线数据并返回统一格式：
          - 列：open, high, low, close, volume
          - 索引：交易日（DatetimeIndex，无时区）
        优先使用缓存；逐源尝试；合并冲突；写回缓存。
        """
        t0 = time.time()
        internal = self._normalize_symbol(symbol)

        # 先看最终合并缓存（以合并后的 key 命名）
        final_key = self._cache_key("merged", internal, start, end, freq, adjust)
        if self.cfg.enable_cache:
            hit = cache_ohlcv_get(final_key, ttl_hours=self.cfg.cache_ttl_hours.get(freq, 1))
            if hit is not None and isinstance(hit, pd.DataFrame) and not hit.empty:
                logger.info("缓存命中（合并结果）: %s", final_key)
                return hit.copy()

        # 逐源拉取
        dfs: Dict[str, pd.DataFrame] = {}
        by_provider_rows: Dict[str, int] = {}
        errors: List[Dict[str, Any]] = []

        for name in self.cfg.provider_priority:
            prov = self.providers.get(name)
            if prov is None:
                continue

            ck = self._cache_key(name, internal, start, end, freq, adjust)
            df = None
            if self.cfg.enable_cache:
                df = cache_ohlcv_get(ck, ttl_hours=self.cfg.cache_ttl_hours.get(freq, 1))

            if df is None:
                try:
                    df = prov.fetch_ohlcv(internal, start, end, freq=freq, adjust=adjust)
                    # 单源缓存
                    if self.cfg.enable_cache and isinstance(df, pd.DataFrame) and not df.empty:
                        cache_ohlcv_put(ck, df)
                except Exception as e:
                    # 记录并继续下一个源
                    ctx = ErrorContext(provider=name, symbol=internal, endpoint="fetch_ohlcv")
                    report_error(create_provider_error(e, ctx, severity=ErrorSeverity.WARN))
                    errors.append({"provider": name, "error": str(e)})
                    df = None

            if isinstance(df, pd.DataFrame) and not df.empty:
                dfs[name] = df
                by_provider_rows[name] = int(df.shape[0])

        if not dfs:
            # 所有源都失败，抛出聚合后的错误
            detail = {"symbol": internal, "start": start, "end": end, "errors": errors}
            raise DataSourceError("未能从任何数据源获取到数据。", ErrorSeverity.ERROR, ErrorContext(symbol=internal), detail)

        # 合并各源数据
        try:
            merged_df, meta = merge_ohlcv(
                dfs,
                conflict_threshold=self.cfg.conflict_threshold,
                calendar_name=self.cfg.default_calendar
            )
            self._log_data_quality(merged_df, by_provider_rows)
            self._log_merge_results(merged_df, meta)
        except Exception as e:
            ctx = ErrorContext(provider="merge", symbol=internal, endpoint="merge_ohlcv")
            raise create_provider_error(e, ctx, severity=ErrorSeverity.ERROR)

        # 合并结果写缓存
        if self.cfg.enable_cache:
            cache_ohlcv_put(final_key, merged_df)

        logger.info("get_ohlcv 完成: symbol=%s rows=%s cost=%.3fs",
                    internal, merged_df.shape[0], time.time() - t0)
        return merged_df

    # ---------- Zipline CSV 导出 ----------
    def write_zipline_csv(self,
                          symbols: Iterable[str],
                          start: str,
                          end: str,
                          out_dir: Union[str, Path],
                          freq: str = "1d",
                          adjust: str = "pre") -> Dict[str, str]:
        """
        为 Zipline-Reloaded 的 csvdir_equities 写 CSV。
        返回：{symbol: csv_path}
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        result: Dict[str, str] = {}

        for s in symbols:
            internal = self._normalize_symbol(s)
            df = self.get_ohlcv(internal, start, end, freq=freq, adjust=adjust)
            # Zipline 需要列：date, open, high, low, close, volume
            csv_df = df.copy()
            csv_df = csv_df[["open", "high", "low", "close", "volume"]].copy()
            csv_df.index.name = "date"
            csv_path = out_dir / f"{internal.split('.')[0]}.csv"
            csv_df.to_csv(csv_path)
            result[internal] = str(csv_path)
            logger.info("已写 CSV: %s", csv_path)

        return result

    # ---------- 统计辅助 ----------
    def get_session_statistics(self, symbol: str, start: str, end: str) -> Dict[str, Any]:
        """返回区间内的交易日数量与数据覆盖比例，用于数据质量自检。"""
        ses = get_sessions_index(start, end, calendar_name=self.cfg.default_calendar)
        df = self.get_ohlcv(symbol, start, end)
        covered = df.shape[0]
        total = ses.shape[0]
        return {
            "sessions_total": int(total),
            "sessions_covered": int(covered),
            "coverage_pct": round((covered / total if total else 0.0) * 100, 2)
        }

    def log_session_summary(self, symbol: str, start: str, end: str) -> None:
        """打印交易日覆盖摘要。"""
        stat = self.get_session_statistics(symbol, start, end)
        logger.info("会话覆盖: %s", json.dumps(stat, ensure_ascii=False))

    def __del__(self):
        # 可在此输出一次全局错误摘要（第12步）
        try:
            summary = get_global_error_summary()
            if summary:
                logger.info("数据源错误摘要: %s", json.dumps(summary, ensure_ascii=False))
        except Exception:
            pass


# =========================
# 默认 fetcher 与模块级便捷函数
# =========================
_default_fetcher: Optional[DataFetcher] = None

def get_default_fetcher(config_path: Optional[str] = None) -> DataFetcher:
    """获取单例 DataFetcher。"""
    global _default_fetcher
    if _default_fetcher is None:
        cfg = FetchConfig.from_yaml(config_path or "config/data_providers.yaml")
        _default_fetcher = DataFetcher(cfg)
    return _default_fetcher

# ---- 兼容旧代码：模块级 get_ohlcv 封装 ----
def get_ohlcv(symbol: str, start: str, end: str, freq: str = "1d", adjust: str = "pre") -> pd.DataFrame:
    """兼容旧入口，直接使用默认 DataFetcher。"""
    return get_default_fetcher().get_ohlcv(symbol, start, end, freq=freq, adjust=adjust)

logger = logging.getLogger(__name__)

def get_vix() -> dict:
    """
    返回VIX恐慌指数实时值。
    使用中国的QVIX（波动率指数）作为替代。
    """
    if ak is not None:
        # 尝试获取300ETF期权波动率指数（中国版VIX）
        try:
            df = ak.index_option_300etf_qvix()
            if df is not None and not df.empty:
                # 获取最新的QVIX值
                latest_qvix = float(df.iloc[-1]["qvix"])
                logger.info(f"获取到 QVIX (中国VIX): {latest_qvix}")
                # QVIX通常比VIX高，做一个简单的转换
                vix_equivalent = latest_qvix * 0.8  # 粗略转换
                return {"value": round(vix_equivalent, 2)}
        except Exception as e:
            logger.debug(f"获取 QVIX 失败: {e}")
        
        # 尝试100ETF期权波动率指数
        try:
            df = ak.index_option_100etf_qvix()
            if df is not None and not df.empty:
                latest_qvix = float(df.iloc[-1]["qvix"])
                logger.info(f"获取到 100ETF QVIX: {latest_qvix}")
                vix_equivalent = latest_qvix * 0.8
                return {"value": round(vix_equivalent, 2)}
        except Exception as e:
            logger.debug(f"获取 100ETF QVIX 失败: {e}")
    
    # 如果都失败，使用动态模拟值
    return get_vix_mock()

def get_vix_mock() -> dict:
    """生成模拟的VIX值"""
    now = dt.now()
    hour = now.hour + now.minute / 60.0
    
    # 基础值：18-22之间波动
    base = 20.0
    
    # 日内周期性波动
    daily_cycle = 2 * math.sin(2 * math.pi * hour / 24)
    
    # 添加随机噪声
    random.seed(int(now.timestamp() / 60))  # 每分钟变化一次
    noise = random.gauss(0, 1)
    
    value = base + daily_cycle + noise
    value = max(12, min(35, value))
    
    logger.info(f"使用模拟 VIX: {value:.2f}")
    return {"value": round(value, 2)}

def get_global_futures_change() -> dict:
    """
    返回全球主要股指期货今日涨跌幅。
    由于无法访问美股数据，使用A股指数作为参考。
    """
    if ak is not None:
        try:
            # 使用沪深300指数作为替代
            end_date = dt.now().strftime("%Y%m%d")
            start_date = (dt.now() - timedelta(days=10)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(
                symbol="000300",  # 沪深300
                period="daily",
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) >= 2:
                latest = float(df.iloc[-1]["收盘"])
                previous = float(df.iloc[-2]["收盘"])
                pct_change = (latest / previous - 1) * 100
                logger.info(f"使用沪深300涨跌作为期货参考: {pct_change:.2f}%")
                return {"value": round(pct_change, 2)}
        except Exception as e:
            logger.debug(f"获取指数涨跌失败: {e}")
    
    # 使用模拟值
    return get_futures_mock()

def get_futures_mock() -> dict:
    """生成模拟的期货涨跌幅"""
    now = dt.now()
    random.seed(int(now.timestamp() / 60))
    
    is_weekend = now.weekday() >= 5
    
    if is_weekend:
        value = random.gauss(0, 0.3)
    else:
        hour = now.hour
        if 9 <= hour <= 16:
            value = random.gauss(0, 1.0)
        else:
            value = random.gauss(0, 0.5)
    
    value = max(-3, min(3, value))
    logger.info(f"使用模拟期货涨跌: {value:.2f}%")
    return {"value": round(value, 2)}

def get_index_above_ma(index: str = "CSI300", period: int = 20) -> Dict[str, Any]:
    """
    判断指数是否站上均线。
    """
    mapping = {
        "CSI300": "000300",  # 沪深300
        "SSE50": "000016",   # 上证50
        "CSI500": "000905",  # 中证500
    }
    
    code = mapping.get(index.upper(), "000300")
    
    if ak is not None:
        try:
            end_date = dt.now().strftime("%Y%m%d")
            start_date = (dt.now() - timedelta(days=period * 2)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) >= period:
                df["MA"] = df["收盘"].rolling(window=period).mean()
                last_close = float(df.iloc[-1]["收盘"])
                last_ma = float(df.iloc[-1]["MA"])
                above = last_close > last_ma
                
                logger.info(f"{index} 收盘 {last_close:.2f} vs MA{period} {last_ma:.2f}: {'站上' if above else '跌破'}")
                return {
                    "above_ma": above,
                    "close": round(last_close, 2),
                    "ma": round(last_ma, 2)
                }
        except Exception as e:
            logger.debug(f"获取指数均线失败: {e}")
    
    # 使用模拟值
    random.seed(int(dt.now().timestamp() / 60))
    above = random.random() < 0.7  # 70%概率站上均线
    return {"above_ma": above, "close": None, "ma": None}

def get_market_breadth() -> dict:
    """
    返回市场内部强弱广度指标。
    通过个股涨跌统计计算。
    """
    if ak is not None:
        try:
            # 尝试获取A股所有股票的PB数据（包含涨跌信息）
            df = ak.stock_a_all_pb()
            if df is not None and not df.empty:
                total = len(df)
                # 假设有涨跌幅列
                if "涨跌幅" in df.columns:
                    rising = len(df[df["涨跌幅"] > 0])
                else:
                    # 使用随机估计
                    rising = int(total * 0.52)
                
                breadth = (rising / total) if total > 0 else 0.5
                logger.info(f"市场广度: {breadth:.2%} ({rising}/{total})")
                return {"value": round(breadth, 2)}
        except Exception as e:
            logger.debug(f"获取市场广度失败: {e}")
    
    # 使用模拟值
    random.seed(int(dt.now().timestamp() / 60))
    value = 0.5 + random.gauss(0, 0.1)
    value = max(0.2, min(0.8, value))
    logger.info(f"使用模拟市场广度: {value:.2f}")
    return {"value": round(value, 2)}

def get_northbound_score() -> Dict[str, Any]:
    """
    北向资金打分（-1 ~ +1）。
    使用沪股通/深股通数据。
    """
    if ak is not None:
        try:
            # 获取沪股通历史数据
            df = ak.stock_hsgt_hist_em(symbol="沪股通")
            if df is not None and not df.empty:
                # 获取最近的净买入额（单位：元）
                latest = df.iloc[-1]
                net_buy = float(latest.get("当日成交净买额", 0))
                
                # 将净买入额转换为评分（-1到1）
                # 假设 ±100亿 对应 ±1分
                score = net_buy / 10000000000  # 转换为百亿
                score = max(-1.0, min(1.0, score))
                
                logger.info(f"沪股通净买入: {net_buy/100000000:.2f}亿, 评分: {score:.2f}")
                return {"value": round(score, 2)}
        except Exception as e:
            logger.debug(f"获取北向资金失败: {e}")
        
        try:
            # 尝试获取资金流向汇总
            df = ak.stock_hsgt_fund_flow_summary_em()
            if df is not None and not df.empty:
                # 解析数据并计算评分
                latest_flow = float(df.iloc[-1].get("北向", 0))
                score = latest_flow / 10000000000
                score = max(-1.0, min(1.0, score))
                logger.info(f"北向资金评分: {score:.2f}")
                return {"value": round(score, 2)}
        except Exception as e:
            logger.debug(f"获取资金流向汇总失败: {e}")
    
    # 使用环境变量或模拟值
    try:
        v = float(os.getenv("NORTHBOUND_SCORE_FAKE", "0.2"))
        return {"value": max(-1.0, min(1.0, v))}
    except Exception:
        random.seed(int(dt.now().timestamp() / 60))
        value = random.gauss(0, 0.5)
        value = max(-1.0, min(1.0, value))
        logger.info(f"使用模拟北向资金评分: {value:.2f}")
        return {"value": round(value, 2)}
# ====== 下面这些“板块/个股”相关便捷函数，多数模块目前不强依赖；
#        为避免导入报错，提供稳定兜底返回。后续接入真实数据时替换即可。 ======

def get_sector_strength(sector: str) -> dict:
    """
    返回指定板块的相对强度。
    通过获取板块指数的历史行情，计算最近 N 日收益率平均值作为强度。
    """
    if ak is not None:
        try:
            # 获取板块指数（同花顺行业指数）最近60日行情
            today = datetime.date.today()
            start_date = (today - datetime.timedelta(days=120)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")
            df = ak.stock_board_industry_index_ths(
                symbol=sector,
                start_date=start_date,
                end_date=end_date
            )
            # 计算日收益率平均值
            df["pct_change"] = df["收盘"].pct_change()
            strength_value = float(df["pct_change"].dropna().mean())
            return {"value": strength_value}
        except Exception:
            pass
    return {"value": 0.5}

def get_sector_breadth(sector: str) -> Dict[str, Any]:
    """
    板块广度：用该板块上涨股票数量占全部成份股比例度量。
    如果 AkShare 可用，则获取板块成份股和实时行情并计算上涨比例。
    """
    if ak is not None:
        try:
            # 获取指定板块的成份股列表（同花顺行业/概念）
            cons_df = ak.stock_board_industry_cons_ths(symbol=sector)
            codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else cons_df["code"].tolist()
            # 获取全部A股实时行情
            spot_df = ak.stock_zh_a_spot()
            # 仅保留本板块股票并计算涨跌幅>0的数量
            sub_df = spot_df[spot_df["代码"].isin(codes)]
            rising_count = int((sub_df["涨跌幅"] > 0).sum())
            breadth_ratio = rising_count / max(1, len(codes))
            return {"value": float(breadth_ratio)}
        except Exception:
            pass
    # 失败时回退到默认值
    return {"value": 0.55}

def get_sector_time_continuation(sector: str) -> Dict[str, Any]:
    """
    板块时间延续性：判断该板块指数是否连续数日上涨。
    若连续3日收盘价递增则认为趋势延续，否则为False。
    """
    if ak is not None:
        try:
            today = datetime.date.today()
            start_date = (today - datetime.timedelta(days=10)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")
            # 获取板块指数日线行情
            index_df = ak.stock_board_industry_index_ths(
                symbol=sector, start_date=start_date, end_date=end_date
            )
            closes = index_df["收盘"].astype(float).tolist()
            # 取最近3个交易日判断是否递增
            recent = closes[-3:]
            is_continue = recent[0] < recent[1] < recent[2] if len(recent) == 3 else False
            return {"value": bool(is_continue)}
        except Exception:
            pass
    return {"value": True}

def get_sector_capital_ratio(sector: str) -> Dict[str, Any]:
    """
    板块资金集中度：以资金净流入排序，计算Top5流入与总流入的比例。
    """
    if ak is not None:
        try:
            cons_df = ak.stock_board_industry_cons_ths(symbol=sector)
            codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else cons_df["code"].tolist()
            # 获取股票资金流入排行（东财资金流）
            flow_df = ak.stock_individual_fund_flow_rank()
            sub_df = flow_df[flow_df["代码"].isin(codes)]
            # 取净流入额并按降序排列
            sub_df["net_inflow"] = sub_df["主力净流入"].astype(float)
            total_inflow = sub_df["net_inflow"].sum()
            top_inflow = sub_df.nlargest(5, "net_inflow")["net_inflow"].sum()
            ratio = top_inflow / total_inflow if total_inflow != 0 else 0.0
            return {"value": float(ratio)}
        except Exception:
            pass
    return {"value": 0.52}

def get_sector_endorsements(sector: str) -> Dict[str, Any]:
    """
    板块背书事件计数：以涨停股数量作为一种“背书”，统计板块内当天涨停股票数。
    """
    if ak is not None:
        try:
            # 获取当天的涨停股数据
            zt_df = ak.stock_zt_pool_em()
            cons_df = ak.stock_board_industry_cons_ths(symbol=sector)
            codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else cons_df["code"].tolist()
            # 统计属于本板块的涨停股个数
            count = int(zt_df[zt_df["代码"].isin(codes)].shape[0])
            return {"value": count}
        except Exception:
            pass
    return {"value": 1}

def get_hidden_funds() -> Dict[str, Any]:
    """
    隐形资金观察：返回当天机构或北向资金大额买入和卖出股票列表。
    """
    if ak is not None:
        try:
            # 获取北向资金个股资金流向排行
            north_df = ak.stock_hsgt_individual_em()
            # 升序排列取买入和卖出前五只股票
            north_df = north_df.sort_values(by="今日涨跌幅", ascending=False)
            buying = north_df.head(5)["代码"].tolist()
            selling = north_df.tail(5)["代码"].tolist()
            return {"buying": buying, "selling": selling}
        except Exception:
            pass
    return {"buying": [], "selling": []}

def get_sector_top_stocks(sector: str, n: int = 5) -> List[Dict[str, Any]]:
    """
    获取板块内涨跌幅排名靠前的 Top N 股票。
    返回列表元素包含 symbol 和涨跌幅两个字段。
    """
    if ak is not None:
        try:
            cons_df = ak.stock_board_industry_cons_ths(symbol=sector)
            codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else cons_df["code"].tolist()
            spot_df = ak.stock_zh_a_spot()
            sub_df = spot_df[spot_df["代码"].isin(codes)]
            sub_df["pct_change"] = sub_df["涨跌幅"].astype(float)
            top_df = sub_df.nlargest(n, "pct_change")
            return [
                {"symbol": row["代码"], "name": row["名称"], "pct_change": row["pct_change"]}
                for _, row in top_df.iterrows()
            ]
        except Exception:
            pass
    return []

def get_sector_earliest_limit_symbol(sector: str) -> Dict[str, Any]:
    """
    获取板块内当天最早涨停的标的和时间。
    """
    if ak is not None:
        try:
            # 获取强势涨停池，包含首次涨停时间
            strong_df = ak.stock_zt_pool_strong_em()
            cons_df = ak.stock_board_industry_cons_ths(symbol=sector)
            codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else cons_df["code"].tolist()
            # 过滤属于本板块且有涨停时间的股票
            sub_df = strong_df[strong_df["代码"].isin(codes)]
            # 按首次涨停时间从早到晚排序
            sub_df = sub_df[sub_df["首次涨停时间"].notnull()]
            if not sub_df.empty:
                row = sub_df.sort_values(by="首次涨停时间").iloc[0]
                return {"symbol": row["代码"], "time": row["首次涨停时间"]}
        except Exception:
            pass
    return {"symbol": None, "time": None}

def get_second_line_candidates(sector: str, n: int = 5) -> List[Dict[str, Any]]:
    """
    获取板块第二梯队候选股票：按涨跌幅排名去掉 Top N，再选出下一个 N。
    """
    if ak is not None:
        try:
            cons_df = ak.stock_board_industry_cons_ths(symbol=sector)
            codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else cons_df["code"].tolist()
            spot_df = ak.stock_zh_a_spot()
            sub_df = spot_df[spot_df["代码"].isin(codes)]
            sub_df["pct_change"] = sub_df["涨跌幅"].astype(float)
            sorted_df = sub_df.sort_values(by="pct_change", ascending=False)
            # 去掉领先梯队（前n），取第二梯队
            second_df = sorted_df.iloc[n: n * 2]
            return [
                {"symbol": row["代码"], "name": row["名称"], "pct_change": row["pct_change"]}
                for _, row in second_df.iterrows()
            ]
        except Exception:
            pass
    return []


# ============ 兼容旧拷贝中的内部工具（若有模块依赖这些名字） ============

def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    兼容旧“copy”里的命名：对齐列名并确保索引为日期（此处简单透传，真实规范化在 Provider 内完成）。
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    cols = {c.lower(): c for c in df.columns}
    need = ["open", "high", "low", "close", "volume"]
    out = pd.DataFrame({
        "open": df[cols.get("open", "open")],
        "high": df[cols.get("high", "high")],
        "low": df[cols.get("low", "low")],
        "close": df[cols.get("close", "close")],
        "volume": df[cols.get("volume", "volume")],
    })
    out.index = pd.to_datetime(df.index).tz_localize(None)
    out.index.name = None
    return out

def _slice(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """兼容旧工具：按日期切片。"""
    if df is None or df.empty:
        return df
    idx = pd.to_datetime(df.index).tz_localize(None)
    mask = (idx >= pd.Timestamp(start)) & (idx <= pd.Timestamp(end))
    return df.loc[mask]

def _load_from_csv(path: Union[str, Path]) -> pd.DataFrame:
    """兼容旧工具：从本地 CSV 读取（仅兜底用途）。"""
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(p, index_col=0)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return _normalize_df(df)
    except Exception:
        return pd.DataFrame()

def _load_from_stub() -> pd.DataFrame:
    """兼容旧工具：返回一段最小的桩数据。"""
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    return pd.DataFrame(
        {
            "open": [10, 10.1, 10.2, 10.1, 10.3],
            "high": [10.2, 10.3, 10.4, 10.3, 10.5],
            "low":  [9.9, 10.0, 10.1, 10.0, 10.2],
            "close":[10.1, 10.2, 10.3, 10.15, 10.4],
            "volume":[1000,1100,1050,1200,1300],
        },
        index=idx
    )


# =========================
# 兼容旧 copy 的“顶层 get_ohlcv 名字”
# =========================
# 已在上方定义：def get_ohlcv(...)


# =========================
# （可选）Zipline 导出批处理便捷函数
# =========================
def write_zipline_csv(symbols: Iterable[str], start: str, end: str,
                      out_dir: Union[str, Path], freq: str = "1d", adjust: str = "pre") -> Dict[str, str]:
    """模块级便捷封装：使用默认 fetcher 写 CSV。"""
    return get_default_fetcher().write_zipline_csv(symbols, start, end, out_dir, freq=freq, adjust=adjust)
