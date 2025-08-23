# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, Any
from backend.config.settings import load_thresholds
from backend.data.fetcher import (
    get_sector_strength, get_sector_breadth, get_sector_time_continuation,
    get_sector_capital_ratio, get_sector_endorsements, get_hidden_funds
)

@dataclass
class SectorRotation:
    thresholds: dict

    @classmethod
    def load_from_config(cls):
        return cls(load_thresholds())

    def evaluate(self, sector: str = "AI") -> Dict[str, Any]:
        t = self.thresholds.get("rotation", {})
        # 取数（当前为 stub，可离线）
        s = get_sector_strength(sector)
        b = get_sector_breadth(sector)
        tc = get_sector_time_continuation(sector)
        cr = get_sector_capital_ratio(sector)
        en = get_sector_endorsements(sector)
        hf = get_hidden_funds(sector)

        # 阈值
        rank_change_min     = t.get("rank_change_min", 5)
        strength_score_min  = t.get("strength_score_min", 0.70)
        breadth_min         = t.get("breadth_min", 0.60)
        time_days_min       = t.get("time_continuation_days", 2)
        capital_ratio_min   = t.get("capital_ratio_min", 0.50)
        endorse_min_count   = t.get("endorsement_min_count", 1)
        hidden_funds_min    = t.get("hidden_funds_min", 0.55)

        # 六步验证
        checks = {
            "strength": {
                "rank": s["rank"], "rank_change": s["rank_change"], "score": s["score"],
                "min_rank_change": rank_change_min, "min_score": strength_score_min,
                "pass": (s["rank_change"] >= rank_change_min) and (s["score"] >= strength_score_min),
            },
            "breadth": {
                "value": b["pct"], "min": breadth_min,
                "pass": b["pct"] >= breadth_min,
            },
            "time_continuation": {
                "days": tc["days"], "min_days": time_days_min,
                "pass": tc["days"] >= time_days_min,
            },
            "capital_ratio": {
                "value": cr["ratio"], "min": capital_ratio_min,
                "pass": cr["ratio"] >= capital_ratio_min,
            },
            "endorsement": {
                "lupang": en["lupang"], "etf_creation": en["etf_creation"], "northbound": en["northbound"],
                "count": en["count"], "min_count": endorse_min_count,
                "pass": en["count"] >= endorse_min_count,
            },
            "hidden_funds": {
                "value": hf["score"], "min": hidden_funds_min,
                "pass": hf["score"] >= hidden_funds_min,
            },
        }

        passed = sum(1 for c in checks.values() if c["pass"])
        total = len(checks)
        confirm = round(passed / total, 2)

        return {
            "sector": sector,
            "steps": checks,
            "summary": {
                "passed": passed, "total": total, "confirm": confirm,
                "recommend": bool(passed >= 5)  # 示例规则：≥5项通过判定为强轮动
            }
        }
