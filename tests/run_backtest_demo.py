# -*- coding: utf-8 -*-
import sys, json
from backend.core.backtester import SimpleBacktester, _stub_ohlcv

def expect(name, cond, msg=""):
    if cond:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}" + (f" - {msg}" if msg else ""))
        sys.exit(1)

if __name__ == "__main__":
    bt = SimpleBacktester(symbol="002415", sector="AI", mode="breakout", account_size=200000)
    res = bt.run(_stub_ohlcv(50))

    # 至少应有一次交易，且给出汇总
    expect("backtest.has_trades", res["summary"]["n_trades"] >= 1, json.dumps(res["summary"], ensure_ascii=False))
    expect("backtest.has_summary_fields",
           all(k in res["summary"] for k in ("win_rate", "pnl_total_per_share", "equity_points")),
           json.dumps(res["summary"], ensure_ascii=False))

    print("[DONE] 示例回测输出：")
    print(json.dumps(res, ensure_ascii=False, indent=2))
