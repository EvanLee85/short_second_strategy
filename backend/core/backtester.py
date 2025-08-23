# -*- coding: utf-8 -*-
"""
最小回测器（单标的、单策略、固定止盈/止损）
- 仅依赖现有 evaluate_signal / RiskManager，不改动其它模块
- 默认使用入参 ohlcv（字典：t/o/h/l/c/v），未提供则用自带 stub
"""

from typing import Dict, Any, List
import pandas as pd

from .entry_signals import evaluate_signal, load_thresholds  # 复用现有信号判定
from .risk_manager import RiskManager       # 复用三闸门/止盈止损/仓位逻辑


def _stub_ohlcv(n: int = 30, start: str = "2024-01-01") -> Dict[str, List[float]]:
    """用 pandas.date_range 生成合法的连续交易日，避免 2024-01-32 这类非法日期。"""
    idx = pd.date_range(start=start, periods=n, freq="D")   # 连续自然日（示例足够）
    t = [d.strftime("%Y-%m-%d") for d in idx]

    base = 10.0
    # 用 enumerate 保证长度与日期一致
    c = [base + i * 0.2 for i, _ in enumerate(idx)]         # 缓慢上行
    o = [max(0.01, x - 0.05) for x in c]
    h = [x * 1.01 for x in c]
    l = [x * 0.99 for x in c]
    v = [1000 + i * 20 for i, _ in enumerate(idx)]

    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


class SimpleBacktester:
    """极简回测：逐bar以收盘价作判定，次bar内用 high/low 触发固定目标/止损。"""

    def __init__(self,
                 symbol: str = "TEST",
                 sector: str = "AI",
                 mode: str = "breakout",
                 account_size: float = 200_000.0):
        self.symbol = symbol
        self.sector = sector
        self.mode = mode
        self.account_size = float(account_size)
        self.rm = RiskManager.load_from_config()

    def run(self, ohlcv: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = ohlcv or _stub_ohlcv(40)
        df = pd.DataFrame({
            "t": data["t"], "open": data["o"], "high": data["h"],
            "low": data["l"], "close": data["c"], "vol": data["v"]
        })

        cfg = load_thresholds().get("entry", {})
        b_cfg = cfg.get("breakout", {})
        look = int(b_cfg.get("lookback", 20))
        margin = float(b_cfg.get("margin", 0.005))

        in_pos = False
        entry_idx = None
        entry_px = None
        stop_px = None
        tgt_px = None

        trades = []
        equity = [self.account_size]
        cash = self.account_size

        # 逐bar运行：用“当bar收盘价”生成计划；若满足则在“下一bar”内按 high/low 触发
        i = 0
        pending_breakout = None

        while i < len(df):
            # 至少要有若干历史供指标计算
            if i < 5:
                equity.append(cash)
                i += 1
                continue

            # === 1) 判定 + 风控 ===
            sub = df.iloc[: i + 1]
            price = float(sub["close"].iloc[-1])

            # 计算当前子区间的 N 日最高（含当日），并得出突破触发价
            high_n = float(sub["high"].iloc[-look:].max())
            break_price = high_n * (1.0 + margin)

            signal = evaluate_signal({
                "symbol": self.symbol,
                "mode": self.mode,
                "price": price,
                "ohlcv": {
                    "t": list(sub["t"]),
                    "o": list(sub["open"]),
                    "h": list(sub["high"]),
                    "l": list(sub["low"]),
                    "c": list(sub["close"]),
                    "v": list(sub["vol"]),
                }
            })

            gates = self.rm.evaluate_trade_gates({
                "symbol": self.symbol,
                "sector": self.sector,
                "price": price
            })

            # === 2) 若允许入场，则记录入场价格与目标/止损，实际触发放到下一bar ===
            # 非持仓时的入场判定
            if not in_pos and gates.get("pass"):
                if self.mode == "breakout":
                    # 突破：当日只“武装”一个 stop-entry，真正入场放到下一根
                    pending_breakout = break_price
                else:
                    # 其它模式：仍按当天信号真通过才即时入场
                    if signal.get("pass"):
                        entry_idx = i
                        entry_px = price
                        stop_px = float(gates["levels"]["stop"])
                        tgt_px = float(gates["levels"]["target"])
                        in_pos = True
                        pending_breakout = None
                # 这里不扣现金（简化为不算持仓市值），只统计交易盈亏
            # === 3) 下一bar内检查触发 ===
            if pending_breakout is not None and (i + 1 < len(df)) and not in_pos:
                nb = df.iloc[i + 1]
                if float(nb["high"]) >= pending_breakout:
                    # 以突破价入场；用该入场价重新计算风控关口（保持与实际一致）
                    entry_idx = i + 1
                    entry_px = float(pending_breakout)
                    g2 = self.rm.evaluate_trade_gates({
                        "symbol": self.symbol, "sector": self.sector, "price": entry_px
                    })
                    stop_px = float(g2["levels"]["stop"])
                    tgt_px  = float(g2["levels"]["target"])
                    in_pos = True
                    pending_breakout = None
                    
            if in_pos and (i + 1 < len(df)):
                nb = df.iloc[i + 1]
                exit_idx = None
                exit_px = None
                exit_reason = None
                # 先看是否到达目标
                if float(nb["high"]) >= tgt_px:
                    exit_idx = i + 1
                    exit_px = tgt_px
                    exit_reason = "target"
                # 再看是否触发止损
                elif float(nb["low"]) <= stop_px:
                    exit_idx = i + 1
                    exit_px = stop_px
                    exit_reason = "stop"

                if exit_idx is not None:
                    pnl = (exit_px - entry_px)
                    trades.append({
                        "entry_index": int(entry_idx),
                        "exit_index": int(exit_idx),
                        "entry_px": round(entry_px, 4),
                        "exit_px": round(exit_px, 4),
                        "reason": exit_reason,
                        "pnl": round(pnl, 4)
                    })
                    cash += pnl  # 简化：以每股1股计，累计每股盈亏
                    in_pos = False
                    entry_idx = entry_px = stop_px = tgt_px = None

            equity.append(cash)
            i += 1

        wins = sum(1 for t in trades if t["pnl"] > 0)
        wr = (wins / len(trades)) if trades else 0.0
        total_pnl = sum(t["pnl"] for t in trades)

        return {
            "symbol": self.symbol,
            "sector": self.sector,
            "mode": self.mode,
            "trades": trades,
            "summary": {
                "n_trades": len(trades),
                "win_rate": round(wr, 4),
                "pnl_total_per_share": round(total_pnl, 4),
                "equity_points": len(equity)
            }
        }
