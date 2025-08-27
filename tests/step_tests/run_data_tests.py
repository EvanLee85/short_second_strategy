# -*- coding: utf-8 -*-
"""
第 11 步 自测脚本：
- 覆盖 CSV Provider / Stub Provider / 缓存命中
- 只打印通过/失败与关键信息；失败会抛出 AssertionError
运行方式：
    conda activate sss_py311
    export PYTHONPATH=$(pwd)
    python tests/run_data_tests.py
"""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

from backend.data.fetcher import get_ohlcv, CSV_DATA_DIR

PASS, FAIL = "[PASS]", "[FAIL]"


def _prepare_csv(symbol: str) -> None:
    """
    在 data/ohlcv 下生成一个最小 CSV，列：t,o,h,l,c,v
    """
    CSV_DATA_DIR.mkdir(parents=True, exist_ok=True)
    fp = CSV_DATA_DIR / f"{symbol}.csv"
    # 5 根 K 线的演示数据
    df = pd.DataFrame({
        "t": ["2024-01-01","2024-01-02","2024-01-03","2024-01-04","2024-01-05"],
        "o": [10.00, 10.10, 10.20, 10.00, 10.05],
        "h": [10.20, 10.25, 10.30, 10.10, 10.40],
        "l": [9.90, 10.00, 10.10,  9.80, 10.00],
        "c": [10.10, 10.20, 10.00, 10.05, 10.30],
        "v": [1000, 1100, 1200, 1300, 1800],
    })
    df.to_csv(fp, index=False)


def test_csv_provider():
    symbol = "002415"
    _prepare_csv(symbol)
    df, meta = get_ohlcv(symbol, start="2024-01-01", end="2024-01-05",
                         provider="csv", with_meta=True, use_cache=False)
    assert len(df) == 5, "CSV 行数应为 5"
    assert all(col in df.columns for col in ["open","high","low","close","volume"]), "列名不完整"
    assert df.index.is_monotonic_increasing, "索引应升序"
    print(PASS, "csv.provider rows=", meta.rows, "source=", meta.source)


def test_stub_provider():
    df, meta = get_ohlcv("TEST", start="2024-01-01", end="2024-01-10",
                         provider="stub", with_meta=True, use_cache=False)
    assert len(df) == 10, "Stub 行数应为 10（按自然日）"
    assert df.isna().sum().sum() == 0, "Stub 不应产生缺失值"
    print(PASS, "stub.provider rows=", meta.rows, "source=", meta.source)


def test_cache_hit():
    symbol = "002415"
    # 第一次：走 provider 并缓存
    df1, m1 = get_ohlcv(symbol, start="2024-01-01", end="2024-01-05",
                         provider="csv", with_meta=True, use_cache=True, cache_ttl=3600)
    # 第二次：命中缓存
    df2, m2 = get_ohlcv(symbol, start="2024-01-01", end="2024-01-05",
                         provider="csv", with_meta=True, use_cache=True, cache_ttl=3600)
    assert m1.source == "provider", "首次应来自 provider"
    assert m2.source == "cache", "二次应命中 cache"
    assert (df1.values == df2.values).all(), "缓存返回应与首取一致"
    print(PASS, "cache.hit key=", m2.cache_key)


def main():
    try:
        test_csv_provider()
        test_stub_provider()
        test_cache_hit()
        print("\n=== SUMMARY ===")
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(FAIL, str(e))
        print("\n=== SUMMARY ===")
        print("FAILED")


if __name__ == "__main__":
    main()
