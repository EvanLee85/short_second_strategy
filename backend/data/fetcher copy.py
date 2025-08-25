# -*- coding: utf-8 -*-
"""
数据适配层：本阶段仅提供可离线运行的 Stub，后续再接 AkShare/TuShare/券商SDK。
返回的 value 单位/口径要与阈值一致（避免“数值正确但单位不一致”）。
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .cache import (
    make_ohlcv_cache_key,
    get_df_if_fresh,
    put_df,
)

# ---------------------
# 配置（可日后迁到 config）
# ---------------------
CSV_DATA_DIR = Path("data/ohlcv")  # 约定 CSV 数据目录
DEFAULT_CACHE_TTL = 60 * 60 * 12   # 12 小时

def get_vix() -> Dict:
    # TODO: 接入真实数据后替换
    return {"value": 18.4, "source": "stub"}

def get_global_futures_change() -> Dict:
    # 海外期货当日变动（%）；示意值
    return {"value": 0.30, "source": "stub"}

def get_index_above_ma(index: str, period: int) -> Dict:
    # True 表示指数收盘在 MA(period) 之上
    return {"index": index, "period": period, "above_ma": True, "source": "stub"}

def get_market_breadth() -> Dict:
    # 市场广度（%），比如上涨家数占比；示意值
    return {"value": 52.0, "source": "stub"}  # 故意略低，方便看到“软条件不通过”的分支

def get_northbound_score() -> Dict:
    # 北向资金强弱的一个分值/分位（0-100），示意值
    return {"value": 62.0, "source": "stub"}

# -*- coding: utf-8 -*-
# ===== 板块轮动数据（离线 Stub，可跑即可，后续接真数据再替换） =====
from typing import Dict

def get_sector_strength(sector: str) -> Dict:
    # rank: 当日成交额排名（1=最强）；rank_change: 相对前日(或近3日均值)的排名变化（正数=跃升）
    return {"sector": sector, "rank": 3, "rank_change": 6, "score": 0.82, "source": "stub"}

def get_sector_breadth(sector: str) -> Dict:
    # 上涨家数占比（0~1）
    return {"sector": sector, "pct": 0.63, "source": "stub"}

def get_sector_time_continuation(sector: str) -> Dict:
    # 连续强势的天数
    return {"sector": sector, "days": 2, "source": "stub"}

def get_sector_capital_ratio(sector: str) -> Dict:
    # 主力资金/总成交额的比例（0~1）
    return {"sector": sector, "ratio": 0.58, "source": "stub"}

def get_sector_endorsements(sector: str) -> Dict:
    # 背书命中：龙虎榜/ETF申赎/北向（示意全 True）
    d = {"lupang": True, "etf_creation": True, "northbound": True}
    d["count"] = sum(bool(v) for v in d.values())
    d["sector"] = sector
    d["source"] = "stub"
    return d

def get_hidden_funds(sector: str) -> Dict:
    # 自定义“暗度陈仓”分（0~1），例如尾盘净流/大单笔等组合指标
    return {"sector": sector, "score": 0.72, "source": "stub"}

# ===== 一线龙头识别需要的个股数据（离线 Stub） =====
def get_sector_top_stocks(sector: str) -> List[Dict]:
    """
    返回该板块若干只当日重点股票及其基础特征（全部为示意值，可离线运行）。
    字段说明：
      - symbol: 证券代码
      - name:   证券名称
      - turnover_rank: 板块内成交额排名（1=最大）
      - intraday_strength: 日内强度分（0~1）
      - consecutive_limit_days: 连板天数
      - first_limit_minute: 当日最早涨停时间（以分钟计，如 9:42 => 9*60+42=582；未涨停用大数字表示）
    """
    if sector == "AI":
        return [
            {"symbol":"002230","name":"科大讯飞","turnover_rank":1,"intraday_strength":0.86,"consecutive_limit_days":1,"first_limit_minute":585},
            {"symbol":"002415","name":"海康威视","turnover_rank":2,"intraday_strength":0.83,"consecutive_limit_days":2,"first_limit_minute":9999},
            {"symbol":"000063","name":"中兴通讯","turnover_rank":5,"intraday_strength":0.74,"consecutive_limit_days":0,"first_limit_minute":9999},
        ]
    # 其他板块可按需扩展；默认回退一组示例
    return [
        {"symbol":"000001","name":"示例A","turnover_rank":1,"intraday_strength":0.82,"consecutive_limit_days":1,"first_limit_minute":600},
        {"symbol":"000002","name":"示例B","turnover_rank":3,"intraday_strength":0.78,"consecutive_limit_days":0,"first_limit_minute":9999},
    ]

def get_sector_earliest_limit_symbol(sector: str) -> Dict:
    """
    返回板块中“最早涨停”的标的（示意值）。
    """
    return {"symbol":"002230","minute":585, "sector": sector, "source":"stub"}

# ===== 二线龙头筛选所需数据（离线 Stub，可跑即可） =====
def get_second_line_candidates(sector: str) -> List[Dict]:
    """
    返回用于二线筛选的一组候选（示意值；后续接真数据即可）:
      必备字段：
        symbol, name, turnover_rank, mkt_cap(亿元), rs(0~1), net_inflow(亿元),
        pe, distance_ma20(0~1), distance_high(0~1),
        is_st(bool), list_days(int), has_risk_flag(bool)
    """
    if sector == "AI":
        return [
            {"symbol":"002415","name":"海康威视","turnover_rank":4,"mkt_cap":356,"rs":0.87,"net_inflow":2.3,"pe":28.5,"distance_ma20":0.04,"distance_high":0.12,"is_st":False,"list_days":6000,"has_risk_flag":False},
            {"symbol":"000063","name":"中兴通讯","turnover_rank":7,"mkt_cap":170,"rs":0.78,"net_inflow":0.6,"pe":35.0,"distance_ma20":0.06,"distance_high":0.10,"is_st":False,"list_days":5000,"has_risk_flag":False},
            {"symbol":"688001","name":"示例高估值","turnover_rank":9,"mkt_cap":80,"rs":0.81,"net_inflow":0.4,"pe":95.0,"distance_ma20":0.03,"distance_high":0.08,"is_st":False,"list_days":900,"has_risk_flag":False},
            {"symbol":"300999","name":"示例新股","turnover_rank":5,"mkt_cap":120,"rs":0.80,"net_inflow":0.8,"pe":45.0,"distance_ma20":0.05,"distance_high":0.07,"is_st":False,"list_days":15,"has_risk_flag":False},
            {"symbol":"600000","name":"示例风险","turnover_rank":6,"mkt_cap":300,"rs":0.77,"net_inflow":0.7,"pe":20.0,"distance_ma20":0.02,"distance_high":0.05,"is_st":False,"list_days":8000,"has_risk_flag":True},
        ]
    # 其他板块的默认示例
    return [
        {"symbol":"000001","name":"示例A","turnover_rank":3,"mkt_cap":150,"rs":0.76,"net_inflow":0.9,"pe":25.0,"distance_ma20":0.05,"distance_high":0.10,"is_st":False,"list_days":4000,"has_risk_flag":False},
        {"symbol":"000002","name":"示例B","turnover_rank":10,"mkt_cap":90,"rs":0.80,"net_inflow":0.3,"pe":30.0,"distance_ma20":0.04,"distance_high":0.09,"is_st":False,"list_days":3500,"has_risk_flag":False},
    ]

"""
数据接入层（最小可用版）
- 支持 provider: "csv" / "stub"
- 统一输出：DataFrame，索引为 DatetimeIndex（日期），列为 open/high/low/close/volume
- 仅实现日线 freq='1d'（其他频率后续扩展）
- 支持简单 CSV 缓存（见 backend/data/cache.py）
"""
@dataclass
class FetchMeta:
    """用于测试与排障的元信息"""
    source: str                 # "provider" 或 "cache"
    provider: str               # "csv"/"stub"
    cache_key: Optional[str]    # 实际使用的缓存键（可能为 None）
    cache_path: Optional[str]   # 实际缓存路径（可能为 None）
    rows: int                   # 返回行数


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一列名并排序索引
    输入允许两种列风格：
      1) t, o, h, l, c, v
      2) 索引为日期，列为 open/high/low/close/volume
    """
    if "t" in df.columns:
        df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        df["t"] = pd.to_datetime(df["t"])
        df = df.set_index("t")
    # 保证列顺序
    need = ["open", "high", "low", "close", "volume"]
    for col in need:
        if col not in df.columns:
            raise ValueError(f"缺少列: {col}")
    df = df[need].copy()
    # 索引排序并去重
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _slice(df: pd.DataFrame, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]
    return df


def _load_from_csv(symbol: str) -> pd.DataFrame:
    """
    从 data/ohlcv/{symbol}.csv 读取
    CSV 需包含列：t,o,h,l,c,v（日期可为 YYYY-MM-DD 或 ISO8601）
    """
    fp = CSV_DATA_DIR / f"{symbol}.csv"
    if not fp.exists():
        raise FileNotFoundError(f"CSV 数据不存在: {fp}")
    df = pd.read_csv(fp)
    df = _normalize_df(df)
    return df


def _load_from_stub(symbol: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    """
    生成一段“走势向上+轻噪声”的示例数据，用于离线演示/单测
    """
    s = pd.to_datetime(start or "2024-01-01")
    e = pd.to_datetime(end or "2024-02-29")
    # 日历：用自然日，便于和之前 demo 对齐（需要交易日历时再引入 exchange_calendars）
    t = pd.date_range(s, e, freq="D")
    n = len(t)
    # 基础价格（缓慢上行）
    base = 10 + np.linspace(0, 5, n)
    noise = np.random.RandomState(7).normal(0, 0.05, size=n)  # 固定 seed 便于测试稳定
    close = base + noise
    open_ = close * (1 + np.random.RandomState(8).normal(0, 0.002, size=n))
    high = np.maximum(open_, close) + 0.1
    low = np.minimum(open_, close) - 0.1
    vol = np.random.RandomState(9).randint(1000, 3000, size=n)

    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=t,
    )
    return df


def get_ohlcv(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    freq: str = "1d",
    provider: str = "csv",
    use_cache: bool = True,
    cache_ttl: int = DEFAULT_CACHE_TTL,
    with_meta: bool = False,
) -> pd.DataFrame | Tuple[pd.DataFrame, FetchMeta]:
    """
    统一获取 OHLCV
    - provider: "csv"（生产/联调时读你准备的 CSV），"stub"（测试/演示）
    - 目前仅支持 freq="1d"
    - use_cache=True 时会在 data/cache/ 下按键值缓存
    - with_meta=True 时返回 (df, meta)
    """
    if freq != "1d":
        raise NotImplementedError("仅实现日线 freq='1d'（后续可扩展）")

    cache_key = None
    cache_path = None

    if use_cache:
        cache_key = make_ohlcv_cache_key(symbol, start, end, freq, provider)
        cached = get_df_if_fresh(cache_key, max_age_seconds=cache_ttl)
        if cached is not None:
            df = cached.copy()
            meta = FetchMeta(source="cache", provider=provider, cache_key=cache_key,
                             cache_path=str(Path("data/cache/ohlcv") / cache_key), rows=len(df))
            return (df, meta) if with_meta else df

    # 走真实 provider
    if provider == "csv":
        df = _load_from_csv(symbol)
        df = _slice(df, start, end)
    elif provider == "stub":
        df = _load_from_stub(symbol, start, end)
    else:
        raise ValueError(f"未知 provider: {provider}")

    # 仅保留需要的列并排序
    df = _normalize_df(df)
    df = _slice(df, start, end)

    # 落盘缓存
    if use_cache:
        cache_key = make_ohlcv_cache_key(symbol, start, end, freq, provider)
        cache_path = str(put_df(cache_key, df))

    meta = FetchMeta(
        source="provider",
        provider=provider,
        cache_key=cache_key,
        cache_path=cache_path,
        rows=len(df),
    )
    return (df, meta) if with_meta else df