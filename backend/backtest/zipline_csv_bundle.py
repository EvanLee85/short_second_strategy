# -*- coding: utf-8 -*-
"""
注册 Zipline-Reloaded 的 CSV Bundle，并生成示例 CSV。
CSV 列名采用通用格式：
date,open,high,low,close,volume,dividend,split
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import exchange_calendars as ecals 
from typing import Dict
from backend.backtest.zipline_integration import ensure_zipline_root

# —— 工具：获取/创建 ZIPLINE_ROOT —— #
def get_zipline_root() -> str:
    # 优先使用环境变量；否则放到项目内 var/zipline
    return os.environ.get("ZIPLINE_ROOT") or os.path.join(os.getcwd(), "var", "zipline")

def write_stub_csv(csv_dir: str, symbol: str = "TEST") -> str:
    """
    写入 Zipline csvdir_equities 兼容的示例日线 CSV（A股交易日）。
    必须与注册时的 calendar_name 一致（XSHG）。
    
    改进版：生成包含横盘整理和突破的价格模式
    """
    os.makedirs(csv_dir, exist_ok=True)
    path = os.path.join(csv_dir, f"{symbol}.csv")

    # ★ 使用 XSHG 交易日历，自动排除中国法定休市/节假日
    cal = ecals.get_calendar("XSHG")
    sessions = cal.sessions_in_range("2024-01-01", "2024-03-31")

    # Zipline 要求 index 为无时区日期
    idx = sessions.tz_localize(None) if getattr(sessions, "tz", None) is not None else sessions

    # ★ 改进的价格生成逻辑：创建横盘整理后突破的模式
    n = len(idx)
    prices = np.zeros(n)
    
    # 第一阶段（前20天）：横盘整理在 10-11 之间
    phase1_days = min(20, n)
    prices[:phase1_days] = 10.5 + 0.5 * np.sin(np.linspace(0, 2*np.pi, phase1_days))
    
    # 第二阶段（20-30天）：小幅上涨，准备突破
    if n > 20:
        phase2_days = min(10, n - 20)
        phase2_end = 20 + phase2_days
        prices[20:phase2_end] = np.linspace(10.8, 11.5, phase2_days)
    
    # 第三阶段（30天后）：明显突破并持续上涨
    if n > 30:
        phase3_start = 30
        prices[phase3_start:] = 11.5 + 0.3 * np.arange(n - phase3_start)
    
    # 添加少量噪音使数据更真实
    prices = prices + np.random.normal(0, 0.02, n)
    
    # 生成 OHLC 数据
    close = np.round(prices, 4)
    open_  = np.round(close - 0.05, 4)
    high   = np.round(close + 0.15, 4)  # 高点留有空间
    low    = np.round(open_ - 0.10, 4)
    vol    = np.random.randint(800, 1200, n)

    df = pd.DataFrame({
        "open":  open_,
        "high":  high,
        "low":   low,
        "close": close,
        "volume": vol,
    }, index=idx)
    df.index.name = "date"

    df.to_csv(path, float_format="%.4f")
    
    # 打印数据特征便于调试
    print(f"Generated CSV with {len(df)} trading days from {idx[0]} to {idx[-1]}")
    print(f"Price range: {close.min():.2f} - {close.max():.2f}")
    if n > 30:
        print(f"Price change after day 30: +{((close[-1] / close[30]) - 1) * 100:.1f}%")
    
    return path

# —— 写入 extension.py，注册 csvdir bundle —— #
def install_csv_bundle(bundle_name: str = "sss_csv", csv_dir: str = None) -> Dict[str, str]:
    """
    在 ZIPLINE_ROOT 下写入 extension.py，注册 csvdir bundle。
    注意：通过 register 函数的 calendar_name 参数指定中国A股交易日历
    """
    root = ensure_zipline_root()
    if csv_dir is None:
        csv_dir = os.path.join(os.getcwd(), "data", "zipline_csv")
    os.makedirs(csv_dir, exist_ok=True)

    ext_path = os.path.join(root, "extension.py")
    
    # ★ 修正：csvdir_equities 不接受 calendar_name，只在 register 中指定
    content = f'''# -*- coding: utf-8 -*-
# 自动生成：注册 CSV Bundle (中国A股市场)
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

# 将 {csv_dir} 目录作为数据源
# 使用 XSHG（上海证券交易所）交易日历
register(
    "{bundle_name}", 
    csvdir_equities(["{csv_dir}"]),  # csvdir_equities 只接受目录列表
    calendar_name='XSHG'  # 只在 register 函数中指定 calendar_name
)
'''
    with open(ext_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Created extension.py with calendar_name='XSHG'")
    
    return {"zipline_root": root, "extension": ext_path, "csv_dir": csv_dir, "bundle": bundle_name}

# —— 触发 ingest（通过 python -m zipline 调用 CLI）—— #
def ingest_bundle(bundle_name: str = "sss_csv", csv_dir: str | None = None) -> int:
    import subprocess, os, sys
    from backend.backtest.zipline_integration import ensure_zipline_root

    # 确保 ZIPLINE_ROOT 已设置
    ensure_zipline_root()

    # 组装子进程环境，并注入 CSVDIR
    env = os.environ.copy()
    if csv_dir:
        env["CSVDIR"] = csv_dir
    else:
        # 兜底：使用项目内 data/zipline_csv
        env.setdefault("CSVDIR", os.path.join(os.getcwd(), "data", "zipline_csv"))

    cmd = [sys.executable, "-m", "zipline", "ingest", "-b", bundle_name]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    print(">>> zipline ingest output >>>")
    print(proc.stdout)
    return proc.returncode

# —— 供测试脚本调用的便捷函数 —— #
def setup_and_ingest(bundle: str = "sss_csv", symbol: str = "TEST") -> Dict[str, str]:
    """
    一键：写扩展、产 CSV、ingest。
    """
    meta = install_csv_bundle(bundle)
    csv_path = write_stub_csv(meta["csv_dir"], symbol=symbol)
    rc = ingest_bundle(meta["bundle"], csv_dir=meta["csv_dir"])
    return {**meta, "csv_path": csv_path, "ingest_rc": str(rc)}