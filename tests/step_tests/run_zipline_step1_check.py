# -*- coding: utf-8 -*-
# tests/run_zipline_step1_check.py
from __future__ import annotations
import json
import sys
from backend.backtest.zipline_integration import ensure_zipline_root, get_zipline_env_info

def main():
    try:
        root = ensure_zipline_root()  # 设定 ZIPLINE_ROOT 到 ./var/zipline
        info = get_zipline_env_info() # 导入并收集版本信息
        print("[PASS] zipline.import ok")
        print(json.dumps(info, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"[FAIL] zipline.import - {e!r}")
        sys.exit(1)

if __name__ == "__main__":
    main()
