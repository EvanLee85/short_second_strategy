# -*- coding: utf-8 -*-
"""
简单文件缓存（CSV 版）
- 仅缓存 OHLCV DataFrame，索引为日期（统一列名：open/high/low/close/volume）
- 避免使用 parquet/feather（需要额外依赖），提高环境可移植性
"""
from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


# 默认缓存根目录（可以根据需要改到 config 里）
CACHE_ROOT = Path("data/cache")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _sanitize(s: str) -> str:
    # 简单去除文件名中的不安全字符
    return "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_", ".", "+"))


def make_ohlcv_cache_key(symbol: str, start: Optional[str], end: Optional[str], freq: str, provider: str) -> str:
    # 统一的缓存键规则：ohlcv_{provider}_{symbol}_{start}_{end}_{freq}.csv
    s = start or "none"
    e = end or "none"
    base = f"ohlcv_{provider}_{symbol}_{s}_{e}_{freq}.csv"
    return _sanitize(base)


def cache_path_for(key: str) -> Path:
    p = CACHE_ROOT / "ohlcv" / key
    _ensure_dir(p.parent)
    return p


def get_df_if_fresh(key: str, max_age_seconds: int) -> Optional[pd.DataFrame]:
    """
    如果缓存文件存在且在 max_age_seconds 内，则读出 DataFrame；否则返回 None
    """
    fp = cache_path_for(key)
    if not fp.exists():
        return None
    # 简单 TTL 判断
    age = time.time() - fp.stat().st_mtime
    if age > max_age_seconds:
        return None
    # 读 CSV（索引列为 t）
    df = pd.read_csv(fp, dtype=float, parse_dates=["t"])
    df = df.set_index("t")
    # 列名按约定
    df = df[["open", "high", "low", "close", "volume"]]
    return df


def put_df(key: str, df: pd.DataFrame) -> Path:
    """
    将 DataFrame 写入缓存 CSV，索引输出到列名 t
    """
    fp = cache_path_for(key)
    out = df.copy()
    out = out[["open", "high", "low", "close", "volume"]].copy()
    out = out.reset_index().rename(columns={"index": "t"})
    out.to_csv(fp, index=False)
    return fp
