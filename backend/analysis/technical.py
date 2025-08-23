# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

def ma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n, min_periods=max(2, n//2)).mean()

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """df 需含: high, low, close"""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=max(2, n//2)).mean()

def pct(a: float, b: float) -> float:
    if b == 0: return 0.0
    return (a - b) / b
