# -*- coding: utf-8 -*-
"""
第12步：统一入口（fetcher）测试脚本
---------------------------------
用途：
  1) 生成最小可用配置（仅启用 CSV Provider，默认 XSHG）
  2) 生成一份规范化的 CSV 日线样例数据
  3) 通过 DataFetcher.get_ohlcv() 做一系列一致性/对齐/缓存冒烟测试
  4) 通过 DataFetcher.write_zipline_csv() 验证落盘导出

运行方式（项目根目录）：
  conda activate sss_py311
  export PYTHONPATH=$(pwd)
  python tests/run_fetcher_step12_tests.py
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd

# 确保可导入 backend 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.data.fetcher import get_default_fetcher
from backend.data.normalize import get_sessions_index
import exchange_calendars as xcals


def _print_pass(name, extra=""):
    msg = f"[PASS] {name}"
    if extra:
        msg += f" {extra}"
    print(msg)


def _print_fail(name, extra=""):
    msg = f"[FAIL] {name}"
    if extra:
        msg += f" - {extra}"
    print(msg)
    sys.exit(1)


def _ensure_dirs():
    (ROOT / "config").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "zipline_csv").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "zipline_csv_out").mkdir(parents=True, exist_ok=True)


def _write_min_yaml():
    """
    写入最小化的 data_providers.yaml（仅 CSV 源，开启缓存）。
    注意：csv_provider 会从 csv_dir 读取 CSV。
    """
    cfg = f"""# 自动生成：仅启用 CSV Provider 的最小配置
provider_priority:
  - csv

provider_configs:
  csv:
    csv_dir: "{(ROOT / 'data' / 'zipline_csv').as_posix()}"
    allow_stub: false

enable_cache: true
cache_ttl_hours:
  1d: 24

conflict_threshold: 0.02
freshness_tolerance_days: 3

default_calendar: "XSHG"
default_exchange: "XSHE"
"""
    (ROOT / "config" / "data_providers.yaml").write_text(cfg, encoding="utf-8")


def _write_sample_csv(symbol_no_ex="002415", start="2024-01-02", end="2024-01-10"):
    """
    基于 XSHG 交易日历生成一段日线数据，写入 data/zipline_csv/002415.csv
    列：date,open,high,low,close,volume
    """
    cal = xcals.get_calendar("XSHG")
    ses = get_sessions_index(start, end, "XSHG")  # 已是 tz-naive 的交易日索引

    # 生成一段“递增”的假数据，保证 high>=low & low<=close<=high
    base = 10.0
    rows = []
    for i, ts in enumerate(ses):
        o = base + i * 0.10
        h = o + 0.15
        l = o - 0.12
        c = o + 0.05  # 收盘在当日区间内
        v = 1000 + i * 10
        rows.append([ts.strftime("%Y-%m-%d"), round(o, 4), round(h, 4), round(l, 4), round(c, 4), v])

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    out = ROOT / "data" / "zipline_csv" / f"{symbol_no_ex}.csv"
    df.to_csv(out, index=False)
    return out, len(ses)


def main():
    _ensure_dirs()
    _write_min_yaml()
    csv_path, n_ses = _write_sample_csv()

    # 使用默认入口（会自动读取 config/data_providers.yaml）
    fetcher = get_default_fetcher()

    symbol_a = "002415"         # 无后缀
    symbol_b = "002415.XSHE"    # 内部规范

    start = "2024-01-02"
    end = "2024-01-10"

    # 1) 基础获取：应返回标准列与正确会话数
    t0 = time.time()
    df1 = fetcher.get_ohlcv(symbol_a, start, end, freq="1d", adjust="pre")
    t1 = time.time()

    if df1 is None or df1.empty:
        _print_fail("fetch.basic", "返回空 DataFrame")
    if list(df1.columns) != ["open", "high", "low", "close", "volume"]:
        _print_fail("fetch.columns", f"实际列：{list(df1.columns)}")
    if len(df1) != n_ses:
        _print_fail("fetch.sessions", f"期望 {n_ses}，得到 {len(df1)}")
    if df1.index.tz is not None:
        _print_fail("fetch.index_tz", "索引不应带时区")
    _print_pass("fetch.basic", f"rows={len(df1)} time={ (t1 - t0)*1000:.1f}ms")

    # 2) 代码规范化一致性：无后缀与 .XSHE 应一致
    df2 = fetcher.get_ohlcv(symbol_b, start, end, freq="1d", adjust="pre")
    if not df1.equals(df2):
        _print_fail("normalize.symbol", "无后缀与 .XSHE 结果不一致")
    _print_pass("normalize.symbol")

    # 3) 缓存冒烟：第二次相同请求应明显更快（仅做“相对”判断，不严格卡阈值）
    t2 = time.time()
    df3 = fetcher.get_ohlcv(symbol_a, start, end, freq="1d", adjust="pre")
    t3 = time.time()
    if not df1.equals(df3):
        _print_fail("cache.equality", "二次返回数据与首轮不一致")
    elapsed_first = (t1 - t0) * 1000.0
    elapsed_second = (t3 - t2) * 1000.0
    # 经验阈值：二次时间 < 首次的 60% 视为“命中缓存”（CSV 本地很快，此判断仅作参考）
    if elapsed_second < elapsed_first * 0.6:
        _print_pass("cache.hit", f"{elapsed_second:.1f}ms < {elapsed_first*0.6:.1f}ms")
    else:
        # 缓存实现/路径可能与本判断不完全一致，不作为硬失败，仅提示
        print(f"[INFO] cache.maybe_miss first={elapsed_first:.1f}ms second={elapsed_second:.1f}ms")

    # 4) 导出 Zipline CSV：行数应等于会话数+表头
    out_dir = ROOT / "data" / "zipline_csv_out"
    fetcher.write_zipline_csv([symbol_a], start, end, out_dir.as_posix())
    out_file = out_dir / "002415.csv"
    if not out_file.exists():
        _print_fail("zipline_csv.exists", f"文件不存在：{out_file}")
    # 读取并校验行数
    df_out = pd.read_csv(out_file)
    if len(df_out) != n_ses:
        _print_fail("zipline_csv.rows", f"期望 {n_ses}，得到 {len(df_out)}")
    if list(df_out.columns) != ["date", "open", "high", "low", "close", "volume"]:
        _print_fail("zipline_csv.columns", f"实际列：{list(df_out.columns)}")
    _print_pass("zipline_csv.write", f"rows={len(df_out)}")

    print("\n=== SUMMARY ===")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        _print_fail("unexpected", repr(e))
