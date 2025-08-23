# -*- coding: utf-8 -*-
"""
Step 13-2：CSV Bundle 注册与 ingest 自测
运行：
  conda activate sss_py311
  export PYTHONPATH=$(pwd)
  python tests/run_zipline_step2_bundle.py
"""

import os
import json
from backend.backtest.zipline_csv_bundle import setup_and_ingest, get_zipline_root

def main():
    info = setup_and_ingest(bundle="sss_csv", symbol="TEST")
    root = get_zipline_root()
    data_dir = os.path.join(root, "data", info["bundle"])
    ok = (info["ingest_rc"] == "0") and os.path.isdir(data_dir)

    if ok:
        print("[PASS] zipline.bundle_ingest")
    else:
        print("[FAIL] zipline.bundle_ingest")
    # 打印关键信息（便于排查）
    print(json.dumps({
        "zipline_root": info["zipline_root"],
        "extension": info["extension"],
        "csv_dir": info["csv_dir"],
        "csv_path": info["csv_path"],
        "bundle": info["bundle"],
        "ingest_rc": info["ingest_rc"],
        "data_dir_exists": os.path.isdir(data_dir),
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
