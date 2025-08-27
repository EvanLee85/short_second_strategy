# -*- coding: utf-8 -*-
"""
一次性测试脚本（函数级 + 接口级）
用法：
  1) 另开一个终端启动后端：
       conda activate sss_py311
       export PYTHONPATH=$(pwd)
       python backend/app.py
  2) 运行本脚本：
       conda activate sss_py311
       export PYTHONPATH=$(pwd)
       python tests/run_all_tests.py
说明：
  - 仅打印 PASS/FAIL；失败会给出原因。
  - 接口级测试若服务器未启动，会自动跳过并提示。
"""

import sys, json, time
from typing import Any, Dict

failures = []

def expect(name: str, cond: bool, msg: str = ""):
    if cond:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}" + (f" - {msg}" if msg else ""))
        failures.append(name)

# ========== 函数级（离线） ==========
def test_offline():
    from backend.core.risk_manager import RiskManager
    from backend.core.entry_signals import build_trade_plan

    # 1) 风控三闸门（使用 stub 数据）
    rm = RiskManager.load_from_config()
    gates = rm.evaluate_trade_gates({"symbol":"002415","sector":"AI"})
    try:
        cond = bool(gates["checks"]["rr"]["pass"]) and bool(gates["checks"]["pwin"]["pass"]) and bool(gates["checks"]["ev"]["pass"])
        expect("offline.gates_pass_all", cond, f"checks={gates.get('checks')}")
    except Exception as e:
        expect("offline.gates_pass_all", False, f"exception: {e}")

    # 2) 交易计划（breakout 使用传入 price=12.20 应该 ENTER）
    plan_enter = build_trade_plan({
        "symbol":"002415","sector":"AI","mode":"breakout",
        "price":12.20,"account_size":200000
    })
    expect("offline.plan_breakout_enter", plan_enter.get("decision") == "ENTER",
           f"decision={plan_enter.get('decision')}, signal={plan_enter.get('signal')}")

    # 3) 交易计划（reversal 在现阈值下通常 HOLD；不强制要求）
    plan_rev = build_trade_plan({
        "symbol":"002415","sector":"AI","mode":"reversal",
        "price":11.95,"account_size":200000
    })
    # 只校验结构一致性与决策为 HOLD 或 ENTER
    cond = plan_rev.get("decision") in ("HOLD","ENTER") and ("gates" in plan_rev) and ("signal" in plan_rev)
    expect("offline.plan_reversal_structure", cond, f"decision={plan_rev.get('decision')}")

    # 4) 仓位建议（shares > 0）
    pos = rm.suggest_position({
        "symbol":"002415","sector":"AI","account_size":200000,"price":11.95
    })
    try:
        shares = int(pos["position"]["shares"])
        expect("offline.position_positive_shares", shares > 0, f"shares={shares}, pos={pos}")
    except Exception as e:
        expect("offline.position_positive_shares", False, f"exception: {e}")

    # 5) 撤退剧本（存在关键字段）
    ep = rm.build_exit_plan({
        "symbol":"002415","sector":"AI","entry":11.95,"stop":11.83
    })
    cond = isinstance(ep.get("partials"), list) and "levels" in ep and "trailing" in ep
    expect("offline.exit_plan_structure", cond, f"exit_plan={ep}")

# ========== 接口级（在线） ==========
def test_online():
    try:
        import requests
    except Exception:
        expect("online.import_requests", False, "请先安装 requests: pip install requests")
        return

    base = "http://127.0.0.1:5000/api/v1"

    # 健康检查
    try:
        r = requests.get(f"{base}/health", timeout=2)
        ok = (r.status_code == 200 and isinstance(r.json(), dict) and r.json().get("status") == "ok")
        expect("online.health", ok, f"status={r.status_code}, body={r.text[:200]}")
    except Exception as e:
        expect("online.health", False, f"exception: {e}")
        print("[INFO] 服务器不可用，在线用例将跳过。")
        return

    # 计划聚合（breakout，price=12.20 → 应 ENTER）
    try:
        payload = {"symbol":"002415","sector":"AI","mode":"breakout","price":12.20,"account_size":200000}
        r = requests.post(f"{base}/trades/plan", headers={"Content-Type":"application/json"}, data=json.dumps(payload))
        j = r.json()
        expect("online.plan_breakout_enter", j.get("decision") == "ENTER",
               f"decision={j.get('decision')}, signal={j.get('signal')}")
    except Exception as e:
        expect("online.plan_breakout_enter", False, f"exception: {e}")
        return

    # Paper 开仓（基于上面的计划）
    try:
        r = requests.post(f"{base}/paper/open", headers={"Content-Type":"application/json"}, data=json.dumps(payload))
        j = r.json()
        ok = bool(j.get("open_result",{}).get("ok"))
        expect("online.paper_open", ok, f"open_result={j.get('open_result')}")
    except Exception as e:
        expect("online.paper_open", False, f"exception: {e}")
        return

    # 推进一步（给出高点以触发目标平仓）
    try:
        step_payload = {"price":12.45,"high":12.55,"low":12.30}
        r = requests.post(f"{base}/paper/step", headers={"Content-Type":"application/json"}, data=json.dumps(step_payload))
        j = r.json()
        pos = j.get("state",{}).get("position")
        closed = bool(pos and pos.get("closed"))
        expect("online.paper_step_closed", closed, f"state={j.get('state')}")
    except Exception as e:
        expect("online.paper_step_closed", False, f"exception: {e}")
        return

    # 查看最终状态
    try:
        r = requests.get(f"{base}/paper/state")
        j = r.json()
        pos = j.get("position")
        closed = bool(pos and pos.get("closed"))
        expect("online.paper_state_closed", closed, f"state={j}")
    except Exception as e:
        expect("online.paper_state_closed", False, f"exception: {e}")

if __name__ == "__main__":
    print("=== RUN OFFLINE TESTS ===")
    test_offline()
    print("\n=== RUN ONLINE TESTS ===")
    test_online()

    print("\n=== SUMMARY ===")
    if failures:
        print(f"FAILED: {len(failures)} test(s): {', '.join(failures)}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)
