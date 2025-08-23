# -*- coding: utf-8 -*-
"""
Sentry 自测：离线 + 在线
- 仅打印 [PASS]/[FAIL]，并在服务器不可达时跳过在线用例。
"""

import json
import sys
import traceback

def _pp(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)

def offline_tests():
    from backend.core.sentry import MarketSentry
    ok = True

    try:
        ms = MarketSentry.load_from_config()
        ev = ms.evaluate()
        assert "hard" in ev and "soft" in ev and "summary" in ev
        assert ev["summary"]["hard_pass"] is True
        assert ev["summary"]["halt"] is False
        assert ev["summary"]["allowed"] in (True, False)
        print("[PASS] offline.sentry_structure")
    except Exception:
        ok = False
        print("[FAIL] offline.sentry_structure -", traceback.format_exc().splitlines()[-1])

    return ok

def online_tests():
    ok = True
    try:
        import requests
    except Exception:
        print("[INFO] 缺少 requests，自动跳过在线用例。")
        return True

    base = "http://127.0.0.1:5000/api/v1"

    # 1) 健康检查
    try:
        r = requests.get(f"{base}/health", timeout=2)
        r.raise_for_status()
        print("[PASS] online.health")
    except Exception as e:
        print("[FAIL] online.health -", e)
        print("[INFO] 服务器不可用，在线用例将跳过。")
        return False

    # 2) /sentry/status
    try:
        r = requests.get(f"{base}/sentry/status", timeout=2)
        r.raise_for_status()
        js = r.json()
        assert js["summary"]["halt"] is False
        assert "hard" in js and "soft" in js
        print("[PASS] online.sentry_status")
    except Exception:
        ok = False
        print("[FAIL] online.sentry_status -", traceback.format_exc().splitlines()[-1])

    # 3) /sentry/check
    try:
        r = requests.post(f"{base}/sentry/check", json={}, timeout=2)
        r.raise_for_status()
        js = r.json()
        assert js["halt"] is False
        assert "allowed" in js
        print("[PASS] online.sentry_check")
    except Exception:
        ok = False
        print("[FAIL] online.sentry_check -", traceback.format_exc().splitlines()[-1])

    return ok

def main():
    print("=== RUN SENTRY TESTS ===")
    off = offline_tests()
    on = online_tests()
    print("\n=== SUMMARY ===")
    if off and on:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
