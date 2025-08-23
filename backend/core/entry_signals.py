# -*- coding: utf-8 -*-
"""
买点与分时硬校验（四类）：breakout | pullback | reversal | follow
- 输入通过 HTTP POST 的 JSON；若未提供 ohlcv/intraday，则使用可离线自测的 Stub。
- 输出包含：分时硬校验、策略子型校验、技术参考（MA/ATR）、建议止损位。
"""
from typing import Dict, Any, List
import pandas as pd
from backend.config.settings import load_thresholds
from backend.analysis.technical import ma, atr, pct
from backend.core.risk_manager import RiskManager

def _df_from_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    o = (payload or {}).get("ohlcv")
    if o:
        df = pd.DataFrame({
            "open":  o["o"], "high": o["h"], "low": o["l"], "close": o["c"], "volume": o["v"]
        }, index=pd.to_datetime(o["t"]))
        return df
    # ---- 离线 Stub：构造一段单边略上行的 K 线方便自测 ----
    base = 10.0
    closes = [base + i*0.05 for i in range(40)]  # 40 根
    highs  = [c * (1 + 0.005) for c in closes]
    lows   = [c * (1 - 0.005) for c in closes]
    opens  = [closes[i-1] if i>0 else closes[0]*0.998 for i in range(len(closes))]
    vols   = [1000 + i*10 for i in range(len(closes))]
    # 尾盘 10% 放量（可由阈值控制是否判警）
    for i in range(int(len(vols)*0.9), len(vols)):
        vols[i] *= 1.3
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"open":opens,"high":highs,"low":lows,"close":closes,"volume":vols}, index=idx)

def _intraday_from_payload(payload: Dict[str, Any], defaults: Dict[str, float]) -> Dict[str, float]:
    it = (payload or {}).get("intraday") or {}
    return {
        "early_volume_ratio": float(it.get("first2h_vol_ratio", 0.55)),  # 默认给一个可通过的示例
        "tail_spike_ratio":  float(it.get("close_spike_ratio", 0.18))    # 默认不会触发警戒
    }

def evaluate_signal(payload: Dict[str, Any]) -> Dict[str, Any]:
    tcfg = load_thresholds().get("entry", {})
    intr_cfg   = tcfg.get("intraday", {})
    b_cfg      = tcfg.get("breakout", {})
    p_cfg      = tcfg.get("pullback", {})
    r_cfg      = tcfg.get("reversal", {})
    f_cfg      = tcfg.get("follow", {})

    symbol = (payload or {}).get("symbol", "TEST")
    mode   = (payload or {}).get("mode", "breakout").lower()

    df = _df_from_payload(payload)
    df["ma20"]  = ma(df["close"], int(p_cfg.get("ma_period", 20)))
    df["atr14"] = atr(df, 14)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # ★ 追加：统一用于判定的收盘价（若 payload 提供了 price，则优先使用）
    payload_price = float((payload or {}).get("price") or 0.0)
    close_for_check = payload_price if payload_price > 0 else float(df["close"].iloc[-1])

    # -------- 分时硬指标 --------
    it = _intraday_from_payload(payload, intr_cfg)
    intr_checks = {
        "early_volume_ratio": {
            "value": it["early_volume_ratio"],
            "min": float(intr_cfg.get("early_volume_min_ratio", 0.50)),
            "pass": it["early_volume_ratio"] >= float(intr_cfg.get("early_volume_min_ratio", 0.50))
        },
        "tail_spike_ratio": {
            "value": it["tail_spike_ratio"],
            "max": float(intr_cfg.get("tail_spike_max_ratio", 0.30)),
            "pass": it["tail_spike_ratio"] <= float(intr_cfg.get("tail_spike_max_ratio", 0.30))
        }
    }
    intr_ok = all(x["pass"] for x in intr_checks.values())

    # -------- 子型规则 --------
    mode_checks: Dict[str, Any] = {}
    mode_ok = False

    if mode == "breakout":
        look = int(b_cfg.get("lookback", 20))
        margin = float(b_cfg.get("margin", 0.005))
        high_n = df["high"].iloc[-look:].max()
        eps = 1e-9
        hn = float(high_n * (1 + margin))
        mode_checks = {
            "close_gt_highN": {
                "close": close_for_check, 
                "highN": hn,
                "pass": (close_for_check + eps) >= hn
            }
        }
        mode_ok = mode_checks["close_gt_highN"]["pass"]

    elif mode == "pullback":
        maper = int(p_cfg.get("ma_period", 20))
        tol   = float(p_cfg.get("tolerance", 0.02))
        mode_checks = {
            "above_ma": {
                "close": float(last["close"]), "ma": float(last["ma20"]),
                "pass": float(last["close"]) > float(last["ma20"])
            },
            "needle_to_ma": {
                "low": float(last["low"]), "ma_tol": float(last["ma20"] * (1 + tol)),
                "pass": float(last["low"]) <= float(last["ma20"] * (1 + tol))
            },
            "close_up": {
                "delta_pct": pct(float(last["close"]), float(prev["close"])),
                "pass": pct(float(last["close"]), float(prev["close"])) > 0
            }
        }
        mode_ok = all(x["pass"] for x in mode_checks.values())

    elif mode == "reversal":
        body_pct = abs(float(last["close"]) - float(last["open"])) / float(last["close"])
        need_above_ma = bool(r_cfg.get("need_above_ma", True))
        mode_checks = {
            "body_min": {
                "value": body_pct, "min": float(r_cfg.get("min_body_pct", 0.008)),
                "pass": body_pct >= float(r_cfg.get("min_body_pct", 0.008))
            },
            "close_gt_prev": {
                "value": pct(float(last["close"]), float(prev["close"])),
                "pass": pct(float(last["close"]), float(prev["close"])) > 0
            }
        }
        if need_above_ma:
            mode_checks["above_ma"] = {
                "close": float(last["close"]), "ma": float(last["ma20"]),
                "pass": float(last["close"]) > float(last["ma20"])
            }
        mode_ok = all(x["pass"] for x in mode_checks.values())

    elif mode == "follow":
        gain_margin = float(f_cfg.get("min_gain_margin", 0.003))
        ma_ok = float(last["close"]) > float(last["ma20"]) and float(df["ma20"].iloc[-1]) > float(df["ma20"].iloc[-2])
        mode_checks = {
            "ma_trend_up": {"pass": ma_ok},
            "gain_margin": {
                "value": pct(float(last["close"]), float(prev["close"])),
                "min": gain_margin,
                "pass": pct(float(last["close"]), float(prev["close"])) >= gain_margin
            }
        }
        mode_ok = all(x["pass"] for x in mode_checks.values())

    else:
        mode_checks = {"error": f"unknown mode: {mode}"}
        mode_ok = False

    # 建议止损（ATR 1.5 倍）
    atrv = float(last["atr14"]) if pd.notna(last["atr14"]) else 0.0
    stop = float(last["close"]) - 1.5 * atrv
    risk_pct = (1.5 * atrv / float(last["close"])) if last["close"] else 0.0

    return {
        "symbol": symbol,
        "mode": mode,
        "intraday_checks": intr_checks,
        "mode_checks": mode_checks,
        "tech": {"ma20": float(last["ma20"]), "atr14": atrv},
        "suggested_stop": {"price": round(stop, 4), "risk_pct": round(risk_pct, 4)},
        "pass": bool(intr_ok and mode_ok)
    }

"""
在入场信号模块内，聚合完整交易计划（不新增新文件，遵循 README 架构）。
"""

def build_trade_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入(payload)示例：
      {
        "symbol": "002415",
        "sector": "AI",
        "mode": "reversal",                  # 或 breakout/pullback/follow
        "intraday": {...},                   # 可选：盘中量价提示
        "ohlcv": {...},                      # 可选：离线K线
        "price": 11.95,                      # 可选：计划入场价，不传则由风控内部取 stub close
        "account_size": 200000               # 可选：账户规模，缺省给一个开发期默认
      }
    返回：统一交易计划（信号、风控三闸门、仓位建议、撤退剧本）
    """
    symbol = (payload or {}).get("symbol", "TEST")
    sector = (payload or {}).get("sector", "AI")
    price  = (payload or {}).get("price")
    account_size = float((payload or {}).get("account_size") or 200000.0)  # 开发期默认

    # 1) 入场信号（沿用你现有的 evaluate_signal）
    signal = evaluate_signal(payload)
    signal_pass = bool(signal.get("pass"))

    # 2) 风控三闸门（RR/胜率/净期望）
    rm = RiskManager.load_from_config()
    gates = rm.evaluate_trade_gates({"symbol": symbol, "sector": sector, "price": price})
    gates_pass = bool(gates.get("pass"))

    # 3) 只有在“信号通过 + 三闸门通过”时才给出仓位与撤退剧本；否则仅返回建议为 HOLD
    plan = {
        "symbol": symbol,
        "sector": sector,
        "mode": (payload or {}).get("mode"),
        "signal": signal,
        "gates": gates,
        "decision": "HOLD",          # 默认 HOLD
        "position": None,
        "exit_plan": None
    }

    if signal_pass and gates_pass:
        # 3.1 仓位建议（止损优先用 gates 的 stop）
        pos = rm.suggest_position({
            "symbol": symbol, "sector": sector,
            "account_size": account_size,
            "price": price,
            "stop": gates["levels"]["stop"]
        })
        # 3.2 撤退/执行剧本（目标优先用 gates 的 target）
        ep = rm.build_exit_plan({
            "symbol": symbol, "sector": sector,
            "entry": price,
            "stop": pos["levels"]["stop"],
            "target": gates["levels"]["target"]
        })

        plan.update({
            "decision": "ENTER",     # 允许进场
            "position": pos,
            "exit_plan": ep
        })

    return plan
