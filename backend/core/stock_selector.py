# -*- coding: utf-8 -*-
"""
一线龙头确认（只实现“first-line”，二线筛选在下一步）。
规则要点（与策略一致）：
  1) 成交额排名靠前（如前 N）
  2) “最早涨停”具备显著带动性（可赋权）
  3) 日内强度分 >= 阈值
  4) 约束：若连板天数 >= 3，则不作为入场启动标的一线（但可作为风向标记录）
"""
from dataclasses import dataclass
from typing import Dict, Any, List
from backend.config.settings import load_thresholds
from backend.data.fetcher import get_sector_top_stocks, get_sector_earliest_limit_symbol

@dataclass
class StockSelector:
    thresholds: dict

    @classmethod
    def load_from_config(cls):
        return cls(load_thresholds())

    def identify_first_line(self, sector: str = "AI") -> Dict[str, Any]:
        cfg = self.thresholds.get("first_line", {})
        top_n = int(cfg.get("top_turnover_n", 2))
        min_strength = float(cfg.get("strength_score_min", 0.80))
        earliest_w = float(cfg.get("earliest_limit_weight", 0.50))
        max_boards = int(cfg.get("max_consecutive_boards_for_entry", 2))

        # 取板块候选（离线 stub）
        items: List[Dict] = get_sector_top_stocks(sector)
        earliest = get_sector_earliest_limit_symbol(sector)

        # 先打标签
        for it in items:
            it["tags"] = []
            if it["turnover_rank"] <= top_n:
                it["tags"].append("top_turnover")
            if it["intraday_strength"] >= min_strength:
                it["tags"].append("strong_intraday")
            if it["symbol"] == earliest["symbol"]:
                it["tags"].append("earliest_limit")

        # 计算综合评分（可简单线性加权；仅示意）
        # score = 基础强度 + 最早涨停加权（有则加 earliest_w）
        for it in items:
            score = it["intraday_strength"] + (earliest_w if "earliest_limit" in it["tags"] else 0.0)
            it["score"] = round(min(score, 1.0), 3)  # 限制在 0~1

        # 候选：满足（top_turnover 或 强度达标 或 最早涨停）之一
        candidates = [it for it in items if it["tags"]]
        # 入场约束过滤：连板 >= 3 的只记录不入选
        selected = [it for it in candidates if it["consecutive_limit_days"] < max_boards]
        rejected_3b = [it for it in candidates if it["consecutive_limit_days"] >= max_boards]

        # 排序：按 score 降序、其次 turnover_rank 升序
        selected.sort(key=lambda x: (-x["score"], x["turnover_rank"]))

        summary = {
            "sector": sector,
            "top_n_by_turnover": top_n,
            "min_intraday_strength": min_strength,
            "earliest_limit_weight": earliest_w,
            "max_boards_for_entry": max_boards,
            "selected_count": len(selected),
            "rejected_by_3boards": len(rejected_3b),
        }

        return {
            "summary": summary,
            "selected": selected,
            "rejected_due_to_3_boards_rule": rejected_3b,
            "all_evaluated": items,
        }

    def identify_second_line(self, sector: str = "AI") -> Dict[str, Any]:
        """
        二线筛选：满足“成交额/市值、位置/形态、资金痕迹、估值、RS、避雷”等综合条件。
        规则：硬性避雷先排除；其余打分/计数，通过≥5项即入选（示例逻辑，可按策略细化权重）。
        """
        from backend.data.fetcher import get_second_line_candidates

        cfg = self.thresholds.get("second_line", {})
        rank_max   = int(cfg.get("turnover_rank_max", 8))
        mc_min     = float(cfg.get("mkt_cap_min", 100))
        mc_max     = float(cfg.get("mkt_cap_max", 5000))
        d_ma20_max = float(cfg.get("distance_ma20_max", 0.08))
        d_high_max = float(cfg.get("distance_high_max", 0.15))
        rs_min     = float(cfg.get("rs_min", 0.75))
        inflow_min = float(cfg.get("net_inflow_min", 0.50))
        pe_max     = float(cfg.get("pe_max", 60))

        avoid_cfg  = cfg.get("avoid", {}) or {}
        avoid_st   = bool(avoid_cfg.get("st", True))
        avoid_new  = int(avoid_cfg.get("new_stock_days", 30))
        avoid_risk = bool(avoid_cfg.get("risk_flags", True))

        items: List[Dict] = get_second_line_candidates(sector)
        selected, rejected, evaluated = [], [], []

        for it in items:
            checks = {
                "turnover_rank": it["turnover_rank"] <= rank_max,
                "mkt_cap_band": (mc_min <= it["mkt_cap"] <= mc_max),
                "distance_ma20": it["distance_ma20"] <= d_ma20_max,
                "distance_high": it["distance_high"] <= d_high_max,
                "rs": it["rs"] >= rs_min,
                "net_inflow": it["net_inflow"] >= inflow_min,
                "pe": it["pe"] <= pe_max,
            }
            pass_cnt = sum(1 for v in checks.values() if v)

            # 硬性避雷
            reason_block = None
            if avoid_st and it["is_st"]:
                reason_block = "avoid_st"
            elif avoid_new and it["list_days"] <= avoid_new:
                reason_block = "avoid_new_stock"
            elif avoid_risk and it["has_risk_flag"]:
                reason_block = "avoid_risk_flag"

            rec = {**it, "checks": checks, "pass_count": pass_cnt, "blocked_by": reason_block}
            evaluated.append(rec)

            if reason_block:
                rejected.append(rec)
                continue

            # 通过标准（示例：≥5 项成立）
            if pass_cnt >= 5:
                # 简单评分：通过项数 + 适度加权（例：RS、净流入各+0.2）
                score = pass_cnt + (0.2 if checks["rs"] else 0.0) + (0.2 if checks["net_inflow"] else 0.0)
                rec["score"] = round(score, 3)
                selected.append(rec)
            else:
                rejected.append(rec)

        # 排序：score 降序，其次 turnover_rank 升序
        selected.sort(key=lambda x: (-x.get("score", 0), x["turnover_rank"]))

        summary = {
            "sector": sector,
            "thresholds": {
                "rank_max": rank_max, "mkt_cap": [mc_min, mc_max],
                "distance_ma20_max": d_ma20_max, "distance_high_max": d_high_max,
                "rs_min": rs_min, "net_inflow_min": inflow_min, "pe_max": pe_max,
                "avoid": {"st": avoid_st, "new_stock_days": avoid_new, "risk_flags": avoid_risk}
            },
            "selected_count": len(selected),
            "rejected_count": len(rejected),
            "evaluated": len(evaluated),
        }

        return {"summary": summary, "selected": selected, "rejected": rejected, "all_evaluated": evaluated}
    