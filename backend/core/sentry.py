# -*- coding: utf-8 -*-
"""
MarketSentry：盘中/盘前“停手/熔断”哨兵。
- 仅新增模块，不影响既有接口与风控三闸门。
- 当前版本使用与 MacroFilter 一致的 Stub 指标，后续可接入真实数据源。
"""

from __future__ import annotations
from typing import Dict, Any

# 尝试复用全局阈值加载（若不存在则使用内置默认）
try:
    from backend.core.entry_signals import load_thresholds  # type: ignore
except Exception:
    def load_thresholds() -> Dict[str, Any]:
        return {}

class MarketSentry:
    """市场哨兵：负责硬性熔断与软性情绪评分的统一判定。"""

    def __init__(self, thresholds: Dict[str, Any] | None = None) -> None:
        tcfg = thresholds or {}
        scfg = (tcfg.get("sentry") or {})
        # -------- 硬阈值（任一失败即 halt）--------
        self.vix_max: float = float(scfg.get("hard", {}).get("vix_max", 25.0))
        self.index_dd_max: float = float(scfg.get("hard", {}).get("index_dd_max", 0.08))  # 指数回撤最大值
        # -------- 软阈值（通过越多越好）--------
        self.breadth_min: float = float(scfg.get("soft", {}).get("breadth_min", 55.0))
        self.north_min: float = float(scfg.get("soft", {}).get("northbound_min", 50.0))
        self.sentiment_min: float = float(scfg.get("soft", {}).get("sentiment_min", 0.50))
        self.soft_needed: int = int(scfg.get("soft", {}).get("min_pass_count", 2))  # 建议至少通过 2 项

    # ======= 数据源（当前为 Stub，与 MacroFilter 一致，后续接真数）=======
    def _fetch_stub(self) -> Dict[str, float]:
        """
        返回一组与现有 MacroFilter stub 对齐的演示指标：
        - VIX ~ 18.4（低于 25）
        - 指数回撤（CSI300 相对年内高点回撤）~ 6%
        - 市场宽度 ~ 52%
        - 北向净流入评分 ~ 62
        - 情绪分 ~ 0.58（0~1）
        """
        return {
            "vix": 18.4,
            "index_drawdown": 0.06,
            "breadth": 52.0,
            "northbound": 62.0,
            "sentiment": 0.58,
        }

    # ======= 主判定函数 =======
    def evaluate(self) -> Dict[str, Any]:
        m = self._fetch_stub()

        # 硬指标判定（任何一个失败 -> halt）
        hard = {
            "vix": {
                "value": m["vix"], "max": self.vix_max,
                "pass": m["vix"] <= self.vix_max
            },
            "index_drawdown": {
                "value": m["index_drawdown"], "max": self.index_dd_max,
                "pass": m["index_drawdown"] <= self.index_dd_max
            }
        }
        hard_pass = all(x["pass"] for x in hard.values())

        # 软指标判定（建议：至少通过 soft_needed 项）
        soft = {
            "breadth": {
                "value": m["breadth"], "min": self.breadth_min,
                "pass": m["breadth"] >= self.breadth_min
            },
            "northbound": {
                "value": m["northbound"], "min": self.north_min,
                "pass": m["northbound"] >= self.north_min
            },
            "sentiment": {
                "value": m["sentiment"], "min": self.sentiment_min,
                "pass": m["sentiment"] >= self.sentiment_min
            }
        }
        soft_pass_count = sum(1 for x in soft.values() if x["pass"])

        summary = {
            "hard_pass": bool(hard_pass),
            "soft_pass_count": int(soft_pass_count),
            "soft_total": 3,
            "halt": (not hard_pass),                               # 硬指标失败即停手
            "allowed": (hard_pass and soft_pass_count >= self.soft_needed)  # 建议是否允许执行计划
        }

        return {
            "hard": hard,
            "soft": soft,
            "summary": summary
        }

    # ======= 工厂方法 =======
    @classmethod
    def load_from_config(cls) -> "MarketSentry":
        cfg = load_thresholds()
        return cls(cfg)
