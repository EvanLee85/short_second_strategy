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
    df.index.name = None  # 清除索引名称，保持与原始数据一致
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

# 在现有 cache.py 的基础上，可以添加以下便捷函数：

def clear_cache(provider: Optional[str] = None, max_age_hours: Optional[int] = None) -> int:
    """
    清理缓存文件
    
    参数：
      provider: 只清理指定提供商的缓存，None 表示清理所有
      max_age_hours: 只清理超过指定小时数的文件，None 表示清理所有
    
    返回：
      清理的文件数量
    """
    cache_dir = CACHE_ROOT / "ohlcv"
    if not cache_dir.exists():
        return 0
    
    count = 0
    current_time = time.time()
    
    for file_path in cache_dir.rglob("*.csv"):
        # 按提供商过滤
        if provider and f"_{provider}_" not in file_path.name:
            continue
        
        # 按年龄过滤
        if max_age_hours:
            file_age_hours = (current_time - file_path.stat().st_mtime) / 3600
            if file_age_hours < max_age_hours:
                continue
        
        try:
            file_path.unlink()
            count += 1
        except Exception:
            pass
    
    return count


def get_cache_stats() -> dict:
    """获取缓存统计信息"""
    cache_dir = CACHE_ROOT / "ohlcv"
    if not cache_dir.exists():
        return {"total_files": 0, "total_size_mb": 0, "providers": {}}
    
    stats = {"total_files": 0, "total_size_mb": 0, "providers": {}}
    
    for file_path in cache_dir.rglob("*.csv"):
        stats["total_files"] += 1
        stats["total_size_mb"] += file_path.stat().st_size / (1024 * 1024)
        
        # 提取提供商信息
        parts = file_path.name.split("_")
        if len(parts) >= 2:
            provider = parts[1]
            stats["providers"][provider] = stats["providers"].get(provider, 0) + 1
    
    stats["total_size_mb"] = round(stats["total_size_mb"], 2)
    return stats


# 便捷的封装函数
def cache_ohlcv_get(symbol: str, start: str, end: str, freq: str = "1d", 
                   provider: str = "default", max_age_hours: int = 1) -> Optional[pd.DataFrame]:
    """便捷的缓存读取"""
    key = make_ohlcv_cache_key(symbol, start, end, freq, provider)
    return get_df_if_fresh(key, max_age_hours * 3600)


def cache_ohlcv_put(df: pd.DataFrame, symbol: str, start: str, end: str, 
                   freq: str = "1d", provider: str = "default") -> Path:
    """便捷的缓存写入"""
    key = make_ohlcv_cache_key(symbol, start, end, freq, provider)
    return put_df(key, df)