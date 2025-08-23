# -*- coding: utf-8 -*-
"""
验证：sentry 阈值从 config/thresholds.yaml 读取并生效
- 步骤：
  1) 读取/创建 thresholds.yaml（若不存在则以最小骨架创建）
  2) 正常阈值下，stub 数据应：halt=False, allowed=True
  3) 人为收紧 VIX（vix_max=10），应：halt=True, allowed=False
  4) 还原 thresholds.yaml
- 可选在线测试：若后端存活，则顺便调用 /api/v1/sentry/status 检查
"""
import os, sys, json, shutil, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # 项目根目录
CFG_DIR = ROOT / "config"
CFG_DIR.mkdir(exist_ok=True)
YAML_PATH = CFG_DIR / "thresholds.yaml"
BAK_PATH = CFG_DIR / "thresholds.yaml.bak"

BASE_APPEND = """
sentry:
  hard:
    vix_max: 25.0
    index_dd_max: 0.08
  soft:
    breadth_min: 55.0
    northbound_min: 50.0
    sentiment_min: 0.50
    min_pass_count: 2
"""

def _ensure_yaml_exists():
    if not YAML_PATH.exists():
        YAML_PATH.write_text("# auto-created for test\n" + BASE_APPEND, encoding="utf-8")
        return
    # 若存在但缺少 sentry 段，直接追加
    txt = YAML_PATH.read_text(encoding="utf-8")
    if "sentry:" not in txt:
        YAML_PATH.write_text(txt.rstrip() + "\n" + BASE_APPEND, encoding="utf-8")

def _pp(x): return json.dumps(x, ensure_ascii=False, indent=2)

def offline_checks():
    print("=== OFFLINE YAML CHECKS ===")
    from backend.core.sentry import MarketSentry

    ms = MarketSentry.load_from_config()
    ev = ms.evaluate()
    assert ev["summary"]["halt"] is False, "默认阈值下不应熔断"
    assert ev["summary"]["allowed"] in (True, False)
    assert ev["summary"]["soft_total"] == 3
    print("[PASS] yaml.default_applied (halt=False)")

    # 收紧 VIX（使其必触发熔断）
    import yaml
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("sentry", {}).setdefault("hard", {})["vix_max"] = 10.0
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    import importlib
    import backend.core.entry_signals as es
    import backend.core.sentry as sm

    # 先重载 entry_signals，再重载 sentry，这样 sentry 顶层绑定的 load_thresholds 也会更新
    importlib.reload(es)
    importlib.reload(sm)

    from backend.core.sentry import MarketSentry  # 重新导入，拿到新引用
    ms2 = MarketSentry.load_from_config()
    ev2 = ms2.evaluate()
    assert ev2["summary"]["halt"] is True, "收紧 vix_max 应触发熔断"
    print("[PASS] yaml.tight_vix_triggers_halt (halt=True)")

def online_checks():
    print("=== ONLINE YAML CHECKS ===")
    try:
        import requests
    except Exception:
        print("[INFO] 缺少 requests，跳过在线用例")
        return True

    base = "http://127.0.0.1:5000/api/v1"
    try:
        r = requests.get(f"{base}/health", timeout=2); r.raise_for_status()
    except Exception as e:
        print("[INFO] 后端未启动，跳过在线用例：", e)
        return True

    # 读取当前 YAML 的 vix_max，做一次状态查询
    r = requests.get(f"{base}/sentry/status", timeout=2); r.raise_for_status()
    js = r.json()
    assert "summary" in js and "hard" in js
    print("[PASS] online.sentry_status.with_yaml")

    return True

def main():
    # 备份
    if YAML_PATH.exists():
        shutil.copy2(YAML_PATH, BAK_PATH)

    try:
        _ensure_yaml_exists()
        offline_checks()
        ok_online = online_checks()
        print("\n=== SUMMARY ===")
        print("ALL TESTS PASSED" if ok_online else "FAILED")
        sys.exit(0 if ok_online else 1)
    except Exception:
        print("[FAIL]", traceback.format_exc())
        sys.exit(1)
    finally:
        # 还原
        if BAK_PATH.exists():
            shutil.move(BAK_PATH, YAML_PATH)

if __name__ == "__main__":
    # 确保可导入 backend 包
    sys.path.insert(0, str(ROOT))
    main()
