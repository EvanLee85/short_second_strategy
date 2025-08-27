# -*- coding: utf-8 -*-
"""
step 13-3：运行最小 Zipline 算法，并验证：
- zipline run 正常退出
- 回测期间产生过交易（有至少1笔成交）
- 绩效表存在（有若干日的回测记录）
注意：依赖 step 13-2 已完成（bundle: sss_csv 已 ingest）
"""

import os, sys, json, subprocess, pathlib, pickle
from datetime import datetime
import pandas as pd

PROJ = pathlib.Path(__file__).resolve().parents[1]
ZIPLINE_ROOT = PROJ / "var" / "zipline"
EXT_FILE = ZIPLINE_ROOT / "extension.py"
CSV_DIR = PROJ / "data" / "zipline_csv"
ALGO_FILE = PROJ / "backend" / "zipline" / "algo_breakout_min.py"
OUT_PKL   = ZIPLINE_ROOT / "min_algo_perf.pkl"

def run_cmd(args, env=None, capture_output=True):
    r = subprocess.run(args, env=env, capture_output=capture_output, text=True)
    rc = r.returncode
    out = r.stdout.strip() if r.stdout else ""
    err = r.stderr.strip() if r.stderr else ""
    return rc, out, err

def main():
    # 环境变量：让 zipline 找到 extension.py，并让 csvdir_equities 知道 CSV 目录
    env = os.environ.copy()
    env["ZIPLINE_ROOT"] = str(ZIPLINE_ROOT)
    env["CSVDIR"] = str(CSV_DIR)
    # 确保我们的项目可被 import（若算法文件里需要 import 项目代码，可复用）
    env["PYTHONPATH"] = env.get("PYTHONPATH", "")
    if str(PROJ) not in env["PYTHONPATH"]:
        env["PYTHONPATH"] = f"{PROJ}:{env['PYTHONPATH']}" if env["PYTHONPATH"] else str(PROJ)

    assert EXT_FILE.exists(), f"extension.py 不存在：{EXT_FILE}"
    assert CSV_DIR.exists(),  f"CSV 数据目录不存在：{CSV_DIR}"
    assert ALGO_FILE.exists(),f"回测算法文件不存在：{ALGO_FILE}"

    # 为稳妥，可先尝试 ingest（如果已经存在会快速返回）
    rc_ing, out_ing, err_ing = run_cmd(
        ["zipline", "ingest", "-b", "sss_csv"],
        env=env
    )
    # 不强制要求 ingest 必须 0（有时重复 ingest 也能正常），仅展示信息
    print(">>> zipline ingest rc=", rc_ing)

    # 删除旧结果
    if OUT_PKL.exists():
        OUT_PKL.unlink()

    # 运行 zipline 回测
    # ★ 修改：延后开始日期，确保有足够的历史数据
    # 数据从 2024-01-02 开始，算法需要20天历史数据
    # 所以回测从 2024-02-01 开始更安全（约30个交易日后）
    args = [
        "zipline", "run",
        "-f", str(ALGO_FILE),
        "-b", "sss_csv",
        "--start", "2024-02-01",  # 延后开始日期
        "--end",   "2024-03-29",
        "--capital-base", "100000",
        "--data-frequency", "daily",
        "--no-benchmark",
        "-o", str(OUT_PKL),
    ]
    rc, out, err = run_cmd(args, env=env)
    if rc != 0:
        print("[FAIL] zipline.run rc=", rc)
        print(out)
        print(err)
        sys.exit(1)

    if not OUT_PKL.exists():
        print("[FAIL] 绩效结果文件未生成：", OUT_PKL)
        sys.exit(1)

    # 读取绩效结果（Zipline 输出是一个 pickled 的 pandas.DataFrame）
    try:
        perf = pd.read_pickle(OUT_PKL)
    except Exception as e:
        print("[FAIL] 无法读取绩效结果：", e)
        sys.exit(1)

    # 断言1：有记录
    ok_perf = len(perf) > 0

    # 断言2：产生了至少一笔交易（transactions 列为每日的成交列表）
    tx_col = "transactions"
    n_tx = 0
    if tx_col in perf.columns:
        n_tx = int(sum(len(x) for x in perf[tx_col]))
    ok_tx = n_tx > 0

    # 断言通过/失败打印
    if ok_perf:
        print("[PASS] algo.perf_rows >", len(perf))
    else:
        print("[FAIL] algo.perf_rows == 0")

    if ok_tx:
        print("[PASS] algo.trades_exist n_tx =", n_tx)
    else:
        print("[FAIL] algo.trades_exist n_tx =", n_tx)

    # 汇总输出（便于肉眼核查）
    summary = {
        "first_date": str(perf.index[0]) if ok_perf else None,
        "last_date": str(perf.index[-1]) if ok_perf else None,
        "n_days": int(len(perf)) if ok_perf else 0,
        "n_transactions": int(n_tx),
        "end_portfolio_value": float(perf["portfolio_value"].iloc[-1]) if "portfolio_value" in perf.columns and ok_perf else None,
    }
    print("[SUMMARY]", json.dumps(summary, ensure_ascii=False, indent=2))

    # 最终判定
    if ok_perf and ok_tx:
        print("=== RESULT ===")
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("=== RESULT ===")
        print("FAILED")
        sys.exit(2)

if __name__ == "__main__":
    main()