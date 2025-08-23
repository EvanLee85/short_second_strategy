# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, Any
from backend.config.settings import load_thresholds
from backend.data.fetcher import (
    get_vix, get_global_futures_change, get_index_above_ma,
    get_market_breadth, get_northbound_score
)

@dataclass
class MacroFilter:
    thresholds: dict

    @classmethod
    def load_from_config(cls):
        return cls(load_thresholds())

    def evaluate(self) -> Dict[str, Any]:
        t = self.thresholds.get("macro", {})
        hard = t.get("hard", {})
        soft = t.get("soft", {})

        # --- 拉取数据（当前为 stub，可离线运行） ---
        vix = get_vix()["value"]
        gf  = get_global_futures_change()["value"]
        ma_period = int(soft.get("ma_period", 50))
        idx = get_index_above_ma(index="CSI300", period=ma_period)["above_ma"]
        breadth = get_market_breadth()["value"]
        nb = get_northbound_score()["value"]

        # --- 判定 ---
        hard_checks = {
            "vix": {
                "value": vix, "max": hard.get("vix_max", 25),
                "pass": vix <= hard.get("vix_max", 25)
            },
            "global_futures": {
                "value": gf, "min": hard.get("global_futures_min", -1.5),
                "pass": gf >= hard.get("global_futures_min", -1.5)
            }
        }
        soft_checks = {
            "index_above_ma": {
                "index": "CSI300", "period": ma_period,
                "above": bool(idx), "pass": bool(idx)
            },
            "breadth": {
                "value": breadth, "min": soft.get("breadth_min", 55),
                "pass": breadth >= soft.get("breadth_min", 55)
            },
            "northbound": {
                "value": nb, "min": soft.get("northbound_min", 50),
                "pass": nb >= soft.get("northbound_min", 50)
            }
        }

        hard_pass = all(c["pass"] for c in hard_checks.values())
        soft_pass_cnt = sum(1 for c in soft_checks.values() if c["pass"])

        # 简单裁决逻辑：硬条件全过，且软条件至少过 2 项 => “允许交易”
        trade_ok = bool(hard_pass and soft_pass_cnt >= 2)

        return {
            "hard": hard_checks,
            "soft": soft_checks,
            "summary": {
                "hard_pass": hard_pass,
                "soft_pass_count": soft_pass_cnt,
                "soft_total": len(soft_checks),
                "trade_permitted": trade_ok
            }
        }
