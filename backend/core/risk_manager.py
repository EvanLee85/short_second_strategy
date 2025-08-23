# -*- coding: utf-8 -*-
from typing import Dict, Any
import math
import pandas as pd

from backend.config.settings import load_thresholds
from backend.core.macro_filter import MacroFilter
from backend.core.sector_rotation import SectorRotation
from backend.analysis.technical import atr

_PAPER_STATE = {
    "position": None,   # 当前持仓：{symbol, qty, entry, stop, target, highest, atr, trail_k, closed, exit_*}
    "pnl": 0.0,         # 已实现盈亏（元）
    "logs": []          # 事件日志（字符串）
}

class RiskManager:
    """风控模块：承载三闸门评估（RR / 胜率 / 净期望）"""
    def __init__(self, thresholds: dict):
        self.thresholds = thresholds

    @classmethod
    def load_from_config(cls):
        return cls(load_thresholds())

    def _load_df_stub(self) -> pd.DataFrame:
        base = 10.0
        closes = [base + i*0.05 for i in range(40)]
        highs  = [c * (1 + 0.005) for c in closes]
        lows   = [c * (1 - 0.005) for c in closes]
        opens  = [closes[i-1] if i>0 else closes[0]*0.998 for i in range(len(closes))]
        vols   = [1000 + i*10 for i in range(len(closes))]
        idx = pd.date_range("2024-01-01", periods=len(closes), freq="D")
        df = pd.DataFrame({"open":opens,"high":highs,"low":lows,"close":closes,"volume":vols}, index=idx)
        df["atr14"] = atr(df, 14)
        return df

    def evaluate_trade_gates(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.thresholds.get("gates", {})
        rr_min    = float(cfg.get("rr_min", 2.0))
        pwin_min  = float(cfg.get("pwin_min", 0.60))
        ev_min    = float(cfg.get("ev_net_min", 0.006))
        k_up      = float(cfg.get("atr_k_up", 2.0))
        k_dn      = float(cfg.get("atr_k_dn", 1.0))
        clamp_rng = cfg.get("clamp_pwin", [0.30, 0.80])

        symbol = (payload or {}).get("symbol", "TEST")
        sector = (payload or {}).get("sector", "AI")
        price  = float((payload or {}).get("price") or 0.0)

        df = self._load_df_stub()
        last_close = float(df["close"].iloc[-1])
        atrv = float(df["atr14"].iloc[-1]) if pd.notna(df["atr14"].iloc[-1]) else 0.0
        close = price or last_close

        target = close + k_up * atrv
        stop   = close - k_dn * atrv
        upside   = max(0.0, target - close)
        downside = max(1e-12, close - stop)
        rr = upside / downside if downside > 0 else float("inf")

        eps = 1e-9

        base_p = 0.50
        mf = MacroFilter.load_from_config().evaluate()
        if bool(mf["summary"]["trade_permitted"]):
            base_p += 0.10
        rot = SectorRotation.load_from_config().evaluate(sector or "AI")
        if bool(rot["summary"]["recommend"]):
            base_p += 0.05
        lo, hi = clamp_rng
        pwin = max(lo, min(hi, base_p))

        ev_net = (pwin * upside - (1 - pwin) * downside) / close if close else 0.0

        checks = {
            "rr":   {"value": rr,    "min": rr_min,   "pass": rr + eps >= rr_min},
            "pwin": {"value": pwin,  "min": pwin_min, "pass": pwin >= pwin_min},
            "ev":   {"value": ev_net,"min": ev_min,   "pass": ev_net >= ev_min},
        }
        ok = all(x["pass"] for x in checks.values())

        return {
            "symbol": symbol, "sector": sector,
            "inputs": {"price": close, "atr": atrv, "k_up": k_up, "k_dn": k_dn},
            "levels": {"target": round(target, 4), "stop": round(stop, 4)},
            "metrics": {"rr": round(rr, 3), "pwin": round(pwin, 3), "ev_net": round(ev_net, 4)},
            "checks": checks,
            "pass": bool(ok)
        }

# ===== 内部工具：提供 ATR/close，支持“离线可跑” =====
    def _ensure_price_atr(self, payload: Dict[str, Any]) -> Dict[str, float]:
        """
        优先使用 payload.price；若无，则走与 gates 一致的 stub K 线计算 ATR/close
        返回：{"price": float, "atr": float}
        """
        price = float((payload or {}).get("price") or 0.0)
        if price > 0:
            # 有价格但无 ATR 时，仍需提供一个 ATR：用 stub 近似
            df = self._load_df_stub()
            atrv = float(df["atr14"].iloc[-1]) if pd.notna(df["atr14"].iloc[-1]) else 0.0
            return {"price": price, "atr": atrv}

        # 无价格 → 使用 stub
        df = self._load_df_stub()
        close = float(df["close"].iloc[-1])
        atrv  = float(df["atr14"].iloc[-1]) if pd.notna(df["atr14"].iloc[-1]) else 0.0
        return {"price": close, "atr": atrv}

    # ===== 7.1 仓位管理：给出建议股数/名义金额/最大亏损 等 =====
    def suggest_position(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入(payload)示例：
          {
            "symbol": "002415",
            "sector": "AI",
            "account_size": 200000,    # 账户总资金（元）
            "price": 11.95,            # 计划买入价（元）
            "stop":  11.83             # 计划止损价（可不传：则用 ATR 推导）
          }
        返回：shares/qty/notional/max_loss/risk_pct_used 等
        """
        cfg_all = self.thresholds
        pcfg = cfg_all.get("position", {})
        gcfg = cfg_all.get("gates", {})
        ecfg = cfg_all.get("exit", {})

        lot      = int(pcfg.get("lot_size", 100))
        min_sh   = int(pcfg.get("min_shares", 100))
        fee_pct  = float(pcfg.get("fee_pct", 0.0005))
        slip_pct = float(pcfg.get("slippage_pct", 0.001))
        risk_pct = float(pcfg.get("risk_pct_per_trade", 0.01))
        max_pos  = float(pcfg.get("max_position_pct", 0.25))

        acc = float((payload or {}).get("account_size") or 0.0)
        info = self._ensure_price_atr(payload)
        price, atrv = info["price"], info["atr"]

        # 止损：优先 payload.stop；否则基于 ATR 与 gates/exit 配置推导
        stop = (payload or {}).get("stop")
        if stop is None:
            use_gates_k = bool(ecfg.get("use_gates_k", True))
            k_dn = float(gcfg.get("atr_k_dn", ecfg.get("fallback_atr_k_dn", 1.0))) if use_gates_k else float(ecfg.get("fallback_atr_k_dn", 1.0))
            stop = price - k_dn * atrv
        stop = float(stop)

        # 风险 / 股数估算
        r_per_share = max(1e-6, price - stop)          # 单股风险（含滑点与费用可略微加大）
        r_per_share *= (1 + slip_pct)                  # 滑点近似
        risk_budget = acc * risk_pct                   # 单笔允许亏损
        qty_raw     = math.floor(risk_budget / r_per_share)  # 理论股数
        # 手数对齐与最小股数限制
        qty = max(min_sh, (qty_raw // lot) * lot)

        # 最大仓位限制
        notional = qty * price
        max_notional = acc * max_pos
        if notional > max_notional:
            qty = max(min_sh, (math.floor(max_notional / price) // lot) * lot)
            notional = qty * price

        # 费用估计与最大亏损估计（含双边费率与滑点）
        est_fee = notional * fee_pct * 2
        max_loss = qty * (price - stop) * (1 + slip_pct) + est_fee
        risk_used_pct = max_loss / acc if acc > 0 else 0.0

        # 目标位（用于输出 R 参考）
        use_gates_k = bool(ecfg.get("use_gates_k", True))
        k_up = float(gcfg.get("atr_k_up", ecfg.get("fallback_atr_k_up", 2.0))) if use_gates_k else float(ecfg.get("fallback_atr_k_up", 2.0))
        target = price + k_up * atrv
        r_value = price - stop

        return {
            "symbol": (payload or {}).get("symbol", "TEST"),
            "sector": (payload or {}).get("sector", "AI"),
            "inputs": {"account_size": acc, "price": price, "stop": stop, "atr": atrv},
            "policy": {
                "risk_pct_per_trade": risk_pct,
                "max_position_pct": max_pos,
                "fee_pct": fee_pct,
                "slippage_pct": slip_pct,
                "lot_size": lot
            },
            "position": {
                "shares": int(qty),
                "notional": round(notional, 2),
                "est_fee": round(est_fee, 2),
                "max_loss": round(max_loss, 2),
                "risk_pct_used": round(risk_used_pct, 4)
            },
            "levels": {"target": round(target, 4), "stop": round(stop, 4)},
            "R": {"R_value": round(r_value, 4)}
        }

    # ===== 7.2 撤退规则与执行剧本：产出清晰的计划节点 =====
    def build_exit_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入(payload)示例：
          {
            "symbol":"002415", "sector":"AI",
            "entry":11.95,                 # 进场价
            "stop": 11.83,                 # 初始止损（可选；无则基于 ATR 推导）
            "target": null                 # 目标（可选；无则基于 ATR 推导）
          }
        返回：分批止盈、移动止损、时间止损、复核条件 等
        """
        cfg_all = self.thresholds
        gcfg = cfg_all.get("gates", {})
        ecfg = cfg_all.get("exit", {})
        pcfg = cfg_all.get("position", {})

        info = self._ensure_price_atr(payload)
        atrv = info["atr"]
        entry = float((payload or {}).get("entry") or info["price"])

        # 目标与止损（复用 gates 或 fallback 配置）
        use_gates_k = bool(ecfg.get("use_gates_k", True))
        k_up = float(gcfg.get("atr_k_up", ecfg.get("fallback_atr_k_up", 2.0))) if use_gates_k else float(ecfg.get("fallback_atr_k_up", 2.0))
        k_dn = float(gcfg.get("atr_k_dn", ecfg.get("fallback_atr_k_dn", 1.0))) if use_gates_k else float(ecfg.get("fallback_atr_k_dn", 1.0))

        stop   = (payload or {}).get("stop")
        target = (payload or {}).get("target")
        if stop is None:   stop   = entry - k_dn * atrv
        if target is None: target = entry + k_up * atrv
        stop, target = float(stop), float(target)

        # 分批止盈（以 R 倍与比例定义）
        partials_cfg = ecfg.get("partial_take_profit", []) or []
        partials = []
        for p in partials_cfg:
            r_mul = float(p.get("r_multiple", 1.0))
            pct   = float(p.get("pct", 0.5))
            level = entry + r_mul * (entry - stop)
            partials.append({"at_R": r_mul, "take_pct": pct, "price": round(level, 4)})

        # 移动止损（基于最高价 - trail_atr_k * ATR）
        trail_k = float(ecfg.get("trail_atr_k", 1.5))
        trail_formula = "trailing_stop = rolling_max_high - trail_atr_k * ATR"
        # 时间止损/保本
        time_stop_days = int(ecfg.get("time_stop_days", 5))
        soft_be_R      = float(ecfg.get("soft_break_even_R", 0.8))
        soft_be_price  = entry + soft_be_R * (entry - stop)

        # 复核条件（取宏观与轮动）
        reconsider_cfg = (cfg_all.get("playbook") or {}).get("reconsider_on", {})
        macro_ok = MacroFilter.load_from_config().evaluate()["summary"]["trade_permitted"]
        rot_ok   = SectorRotation.load_from_config().evaluate((payload or {}).get("sector","AI"))["summary"]["recommend"]

        return {
            "symbol": (payload or {}).get("symbol", "TEST"),
            "sector": (payload or {}).get("sector", "AI"),
            "entry": round(entry, 4),
            "levels": {
                "initial_stop": round(stop, 4),
                "target": round(target, 4),
                "soft_break_even": round(soft_be_price, 4)
            },
            "partials": partials,
            "trailing": {
                "trail_atr_k": trail_k,
                "formula": trail_formula,
                "note": "执行时需提供最新最高价与 ATR 实时计算"
            },
            "time_stop": {
                "days": time_stop_days,
                "rule": f"进场后{time_stop_days}日未达到0.5R~1R（示例为0.8R=软保本）则离场或降权"
            },
            "reconsider": {
                "macro_flip_watch": bool(reconsider_cfg.get("macro_flip", True)),
                "rotation_fail_watch": bool(reconsider_cfg.get("rotation_fail", True)),
                "abnormal_gap_dn_watch": bool(reconsider_cfg.get("abnormal_gap_dn", True)),
                "current_macro_permitted": bool(macro_ok),
                "current_rotation_recommend": bool(rot_ok)
            }
        }
    
    # ===== 9.1 重置 / 查询 纸上状态 =====
    def paper_reset(self):
        """重置纸上交易状态（开发期便于反复测试）"""
        global _PAPER_STATE
        _PAPER_STATE = {"position": None, "pnl": 0.0, "logs": []}
        return _PAPER_STATE

    def paper_state(self):
        """查看纸上交易当前状态"""
        return _PAPER_STATE

    # ===== 9.2 开仓：依据聚合计划中的数量/价位建立持仓 =====
    def paper_open(self, *, symbol: str, qty: int, entry: float, stop: float, target: float, atr: float):
        """
        若已有持仓则拒绝；最小可跑，不做撮合细节。
        """
        global _PAPER_STATE
        if _PAPER_STATE["position"] is not None and not _PAPER_STATE["position"].get("closed"):
            return {"ok": False, "error": "position_exists", "state": _PAPER_STATE}

        # trail_k 来自 exit 配置
        ecfg = (self.thresholds.get("exit") or {})
        trail_k = float(ecfg.get("trail_atr_k", 1.5))

        _PAPER_STATE["position"] = {
            "symbol": symbol,
            "qty": int(qty),
            "entry": float(entry),
            "stop": float(stop),
            "target": float(target),
            "highest": float(entry),
            "atr": float(atr),
            "trail_k": trail_k,
            "closed": False,
            "exit_price": None,
            "exit_reason": None,
        }
        _PAPER_STATE["logs"].append(f"OPEN {symbol} qty={qty} entry={entry} stop={stop} target={target}")
        return {"ok": True, "state": _PAPER_STATE}

    # ===== 9.3 推进一步：更新最高价/移动止损；触发止损或止盈则平仓 =====
    def paper_step(self, *, price: float, high: float = None, low: float = None):
        """
        简化执行：
          - 若未持仓直接返回
          - 优先检查止损（含移动止损），再检查止盈；触发则以触发价成交
        """
        global _PAPER_STATE
        pos = _PAPER_STATE["position"]
        if not pos or pos.get("closed"):
            return {"ok": True, "state": _PAPER_STATE}

        px = float(price)
        hi = float(high) if high is not None else px
        lo = float(low)  if low  is not None else px

        # 更新最高价与移动止损
        pos["highest"] = max(pos["highest"], hi)
        trail_stop = pos["highest"] - pos["trail_k"] * pos["atr"]
        curr_stop = max(pos["stop"], trail_stop)

        exit_reason = None
        exit_price = None

        # 先看止损（含移动止损），再看止盈（全量了结示例）
        if lo <= curr_stop:
            exit_reason, exit_price = "stop", curr_stop
        elif hi >= pos["target"]:
            exit_reason, exit_price = "target", pos["target"]

        if exit_reason:
            qty = pos["qty"]
            pnl = (exit_price - pos["entry"]) * qty
            _PAPER_STATE["pnl"] += pnl
            pos.update({"closed": True, "exit_price": exit_price, "exit_reason": exit_reason})
            _PAPER_STATE["logs"].append(
                f"EXIT {pos['symbol']} reason={exit_reason} px={exit_price} pnl={pnl:.2f}"
            )

        return {"ok": True, "state": _PAPER_STATE}
