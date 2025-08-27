# -*- coding: utf-8 -*-
"""
第12步：指标库自测脚本
- 仅打印 PASS/FAIL，不依赖网络与后端服务
- 使用可重复的合成数据，断言数值或关系成立
"""
import math
import json
import numpy as np
import pandas as pd

from backend.core.indicators import (
    ma, ema, atr, rsi, macd, bollinger, stoch_kd, cross_over, cross_under
)

def _make_stub_ohlcv(n=50, start=10.0, step=0.2, seed=42) -> pd.DataFrame:
    """
    生成单调上行的日线数据：
    - close 从 start 开始，每步 +step
    - high=close+0.1, low=close-0.1, open=close-0.05
    - volume 线性增长
    """
    rng = pd.date_range("2024-01-01", periods=n, freq="D")
    close = np.array([start + i * step for i in range(n)], dtype="float64")
    high = close + 0.1
    low = close - 0.1
    open_ = close - 0.05
    volume = np.linspace(1000, 2000, n)

    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=rng
    )
    return df


def _ok(name: str):
    print(f"[PASS] {name}")


def _fail(name: str, msg: str):
    print(f"[FAIL] {name} - {msg}")


def main():
    df = _make_stub_ohlcv(n=60, start=10.0, step=0.2)

    # 1) MA/EMA
    try:
        sma5 = ma(df["close"], 5)
        assert not sma5.isna().all(), "SMA 全为 NA"
        # 最后5个 close 为线性等差：均值应为 (a1 + a5)/2
        last5 = df["close"].iloc[-5:]
        expect = (last5.iloc[0] + last5.iloc[-1]) / 2.0
        assert abs(float(sma5.iloc[-1]) - float(expect)) < 1e-9, f"SMA5 末值不匹配 expect={expect}, got={sma5.iloc[-1]}"
        _ok("ind.ma")
    except AssertionError as e:
        _fail("ind.ma", str(e))

    try:
        e12 = ema(df["close"], 12)
        e26 = ema(df["close"], 26)
        assert float(e12.iloc[-1]) > float(e26.iloc[-1]), "单边上行时，快EMA应大于慢EMA"
        _ok("ind.ema")
    except AssertionError as e:
        _fail("ind.ema", str(e))

    # 2) ATR（本构造下 TR = high-low = 0.2 恒定，ATR 应收敛到 ~0.2）
    try:
        df_atr = _make_stub_ohlcv(n=60, start=10.0, step=0.05)
        a = atr(df_atr, 14)
        assert abs(float(a.iloc[-1]) - 0.2) < 1e-3, f"ATR 末值应接近 0.2, got={a.iloc[-1]}"
        _ok("ind.atr")
    except AssertionError as e:
        _fail("ind.atr", str(e))

    # 3) RSI（单边上行应大于 70）
    try:
        r = rsi(df["close"], 14)
        assert float(r.iloc[-1]) > 70.0, f"RSI 末值应>70, got={r.iloc[-1]}"
        _ok("ind.rsi")
    except AssertionError as e:
        _fail("ind.rsi", str(e))

    # 4) MACD（单边上行，macd>0 且 hist 末值>0）
    try:
        m = macd(df["close"])
        assert float(m["macd"].iloc[-1]) > 0.0, f"macd 应>0, got={m['macd'].iloc[-1]}"
        assert float(m["hist"].iloc[-1]) > 0.0, f"hist 应>0, got={m['hist'].iloc[-1]}"
        _ok("ind.macd")
    except AssertionError as e:
        _fail("ind.macd", str(e))

    # 5) 布林带：upper > mid > lower
    try:
        b = bollinger(df["close"], 20, 2.0)
        last = b.iloc[-1]
        assert last["upper"] > last["mid"] > last["lower"], f"布林带层级错误: {last.to_dict()}"
        _ok("ind.bollinger")
    except AssertionError as e:
        _fail("ind.bollinger", str(e))

    # 6) KD：最后一个 close=最高价，%K 应接近 100
    try:
        kd = stoch_kd(df, k=9, d=3)
        k_last = float(kd["k"].iloc[-1])
        assert k_last > 90.0, f"%K 应接近100（>90），got={k_last}"
        _ok("ind.stoch_kd")
    except AssertionError as e:
        _fail("ind.stoch_kd", str(e))

    # 7) 交叉：构造一个上穿
    try:
        s1 = pd.Series([1.0, 2.0, 3.0, 3.4, 3.6], name="a")
        s2 = pd.Series([5.0, 4.0, 3.5, 3.5, 3.5], name="b")
        assert cross_over(s1, s2) is True, "应判定为上穿"
        assert cross_under(s1, s2) is False, "不应判定为下穿"
        _ok("ind.cross")
    except AssertionError as e:
        _fail("ind.cross", str(e))

    print("\n=== SUMMARY ===")


if __name__ == "__main__":
    main()
