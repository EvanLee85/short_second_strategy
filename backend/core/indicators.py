# -*- coding: utf-8 -*-
"""
统一的技术指标库（第12步）
- 只依赖 pandas / numpy
- 所有函数均为纯计算：输入 Series/DataFrame，返回 Series/DataFrame
- 不做任何数据拉取与缓存
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd


# ===== 基础工具 =====
def pct(a: float, b: float) -> float:
    """安全百分比变化：(a-b)/b；对 b==0 做保护。"""
    if b == 0 or b is None:
        return 0.0
    return (float(a) - float(b)) / float(b)


def _as_series(x) -> pd.Series:
    """把可迭代转为 Series；若已是 Series 原样返回。"""
    if isinstance(x, pd.Series):
        return x.astype(float)
    return pd.Series(x, dtype="float64")


# ===== 移动平均 =====
def ma(close: pd.Series, window: int) -> pd.Series:
    """简单移动平均（SMA）"""
    s = _as_series(close)
    return s.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, span: int, adjust: bool = False) -> pd.Series:
    """指数移动平均（EMA）"""
    s = _as_series(close)
    return s.ewm(span=span, adjust=adjust).mean()


# ===== 波动类 =====
def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range
    需要 DataFrame 包含列：high/low/close
    """
    high = _as_series(df["high"])
    low = _as_series(df["low"])
    close = _as_series(df["close"])
    prev_close = close.shift(1)

    tr1 = (high - low).abs()
    tr2 = (high - prev_close).abs()
    tr3 = (prev_close - low).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder 平滑：等价于 EMA(alpha=1/period)
    atr_series = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr_series


def bollinger(close: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    """
    布林带：返回 mid/upper/lower
    """
    s = _as_series(close)
    mid = s.rolling(window, min_periods=window).mean()
    std = s.rolling(window, min_periods=window).std(ddof=0)
    upper = mid + n_std * std
    lower = mid - n_std * std
    return pd.DataFrame({"mid": mid, "upper": upper, "lower": lower})


# ===== 动量类 =====
def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    s = _as_series(close)
    delta = s.diff()

    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()

    eps = 1e-12
    rs = avg_gain / (avg_loss + eps)
    rsi_val = 100.0 - (100.0 / (1.0 + rs))
    # 无下跌（avg_loss≈0）时，RSI 视为 100
    rsi_val = rsi_val.where(avg_loss > eps, 100.0)
    return rsi_val


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    MACD：返回 macd(快-慢)、signal(DEA)、hist(柱)
    """
    s = _as_series(close)
    ema_fast = ema(s, fast)
    ema_slow = ema(s, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def stoch_kd(df: pd.DataFrame, k: int = 9, d: int = 3) -> pd.DataFrame:
    """
    随机指标 Stochastic K/D
    需要列：high/low/close
    """
    high = _as_series(df["high"])
    low = _as_series(df["low"])
    close = _as_series(df["close"])

    ll = low.rolling(k, min_periods=k).min()
    hh = high.rolling(k, min_periods=k).max()
    # 避免除以0
    denom = (hh - ll).replace(0, np.nan)
    k_fast = (close - ll) / denom * 100.0
    k_slow = k_fast.rolling(d, min_periods=d).mean()
    d_line = k_slow.rolling(d, min_periods=d).mean()
    return pd.DataFrame({"k": k_slow, "d": d_line})


# ===== 辅助（交叉判定等）=====
def cross_over(a: pd.Series, b: pd.Series) -> bool:
    """
    a 上穿 b：当前 a>b 且上一根 a<=b
    """
    a = _as_series(a)
    b = _as_series(b)
    if len(a) < 2 or len(b) < 2:
        return False
    return bool((a.iloc[-1] > b.iloc[-1]) and (a.iloc[-2] <= b.iloc[-2]))


def cross_under(a: pd.Series, b: pd.Series) -> bool:
    """
    a 下穿 b：当前 a<b 且上一根 a>=b
    """
    a = _as_series(a)
    b = _as_series(b)
    if len(a) < 2 or len(b) < 2:
        return False
    return bool((a.iloc[-1] < b.iloc[-1]) and (a.iloc[-2] >= b.iloc[-2]))
