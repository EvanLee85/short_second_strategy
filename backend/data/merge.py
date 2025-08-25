# -*- coding: utf-8 -*-
"""
多源合并与回退（merge）
---------------------------------
用途：
  - 将多个数据源（已各自完成规范化/对齐后的 OHLCV 日线）合并为一条“最终曲线”
  - 自动判断主用数据源、检测新鲜度/完整性
  - 在主源缺失时用备源补齐
  - 当同日数据差异超过阈值时，按优先级与质量分进行决策，并记录冲突日志

输入要求：
  - 所有数据源的 DataFrame 均须满足：
      索引：DatetimeIndex（无时区），按日，完全落在 XSHG 交易日（或其它指定日历）
      列：open, high, low, close, volume（浮点/整型）
  - 如果上一步（normalize.align_and_adjust_ohlcv）已执行过，此处只做合并与冲突处理

输出：
  - merged_df: 合并后的标准 DataFrame（与输入列一致）
  - logs: dict，包含质量评估、回退/冲突明细、主源选择理由等，便于审计
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np

from backend.data.normalize import get_sessions_index


# ---------------------------
# 工具：计算数据源质量评分
# ---------------------------
def _evaluate_provider_quality(
    name: str,
    df: pd.DataFrame,
    sessions: pd.DatetimeIndex,
    freshness_tolerance_days: int = 3,
) -> Dict:
    """
    计算单个数据源的质量指标与简单评分。

    质量维度：
      - 覆盖度 coverage：有 close 的交易日数 / 总会话数
      - 新鲜度 lag_days：距最后会话的滞后会话数（0 表示最新）
      - 异常条目 invalid_rows：如 high<low、close 不在 [low,high]、volume<0
      - 跳变数 spikes：|pct_change(close)| > 20% 的天数（粗略测异常）

    评分（简单可解释）：
      100
      - lag_days * 10
      + coverage * 20
      - invalid_rows * 5
      - spikes * 2
    """
    # 覆盖度
    df_aligned = df.reindex(sessions)
    has_close = df_aligned["close"].notna()
    coverage = float(has_close.sum()) / float(len(sessions) or 1)

    # 新鲜度：以“会话索引位置差”衡量
    last_avail_idx = has_close[::-1].idxmax() if has_close.any() else None
    if last_avail_idx is not None and not pd.isna(last_avail_idx):
        # 会话位置差：最后会话在 sessions 中的下标 - 最后有数据日期的下标
        try:
            last_idx_pos = sessions.get_loc(last_avail_idx)
            lag_days = (len(sessions) - 1) - last_idx_pos
        except KeyError:
            # 若不在会话中（理论不应发生），退化为滞后最大值
            lag_days = freshness_tolerance_days + 1
    else:
        lag_days = freshness_tolerance_days + 1

    # 异常/跳变
    invalid_rows = 0
    spikes = 0
    # 仅对齐后的有效行做检测
    x = df_aligned.copy()
    if not x.empty:
        # 无效：high<low 或 close 不在 [low,high] 或 负量
        cond_invalid = (
            (x["high"] < x["low"])
            | (x["close"] < x["low"])
            | (x["close"] > x["high"])
            | (x["volume"] < 0)
        )
        invalid_rows = int(cond_invalid.fillna(False).sum())

        # 跳变（粗略）
        close_series = x["close"].dropna()
        if len(close_series) > 1:
            pct_chg = close_series.pct_change().abs()
            spikes = int((pct_chg > 0.20).sum())
        else:
            spikes = 0

    score = (
        100.0
        - 10.0 * float(lag_days)
        + 20.0 * float(coverage)
        - 5.0 * float(invalid_rows)
        - 2.0 * float(spikes)
    )

    return {
        "name": name,
        "coverage": round(coverage, 4),
        "lag_days": int(lag_days),
        "invalid_rows": invalid_rows,
        "spikes": spikes,
        "score": round(score, 2),
    }


# ---------------------------
# 主函数：多源合并
# ---------------------------
def merge_ohlcv(
    dataframes: Dict[str, pd.DataFrame],
    start: str,
    end: str,
    calendar_name: str = "XSHG",
    prefer_order: Optional[List[str]] = None,
    freshness_tolerance_days: int = 3,
    conflict_close_pct: float = 0.01,  # 同日 close 相对差 > 1% 视为冲突
    allow_override_on_invalid: bool = True,  # 主源无效行允许被高质量备源覆盖
) -> Tuple[pd.DataFrame, Dict]:
    """
    将多源 OHLCV 合并为“最终曲线”。

    参数：
      dataframes            : {源名: df}，df 已对齐到交易日并有标准列
      start / end           : 合并的起止区间（会被统一裁剪到交易日 sessions）
      calendar_name         : 使用的交易日历（默认 XSHG）
      prefer_order          : 源优先级（列表，越靠前优先级越高）；不传则按 dict 插入顺序
      freshness_tolerance_days : 新鲜度容忍会话数（主源滞后超过此值将被降级）
      conflict_close_pct    : 同日 close 相对差阈值（超阈值记录冲突并偏向高优先源）
      allow_override_on_invalid: 当主源该日明显无效（高低错位等）时允许备源覆盖

    返回：
      (merged_df, logs)
    """
        # 验证输入数据
    for name, df in (dataframes or {}).items():
        if df.empty:
            continue
        
        # 确保数值列为浮点类型
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 确保索引为 datetime 且无时区
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

    # 生成会话索引（无时区）
    sessions = get_sessions_index(start, end, calendar_name=calendar_name)

    # 统一对齐各源（仅重索引，不做填充；假设上一步 normalize 已对齐并填充）
    dfs = {}
    for name, df in (dataframes or {}).items():
        # 基本列校验
        need_cols = {"open", "high", "low", "close", "volume"}
        miss = need_cols - set(map(str.lower, df.columns))
        if miss:
            raise ValueError(f"数据源 {name} 缺少列: {miss}")

        # 列名统一为小写
        x = df.copy()
        x.columns = [c.lower() for c in x.columns]
        # 索引置为无时区日期
        idx = pd.DatetimeIndex(pd.to_datetime(x.index).tz_localize(None))
        x = x.set_index(idx).sort_index()
        # 重索引到 sessions，不填充（以便后续判断缺失/覆盖）
        x = x.reindex(sessions)
        dfs[name] = x

    if not dfs:
        # 无数据源，返回空结果
        empty = pd.DataFrame(index=sessions, columns=["open", "high", "low", "close", "volume"], dtype=float)
        logs = {"providers_quality": [], "primary": None, "fallback_used": 0, "conflicts": []}
        return empty, logs

    # 计算各源质量分
    qualities = [
        _evaluate_provider_quality(name, df, sessions, freshness_tolerance_days=freshness_tolerance_days)
        for name, df in dfs.items()
    ]
    quality_by_name = {q["name"]: q for q in qualities}

    # 确定优先级顺序
    if prefer_order:
        order = [n for n in prefer_order if n in dfs]
        # 追加未显式列出的源，按得分降序排列
        remain = [n for n in dfs.keys() if n not in order]
        remain_sorted = sorted(remain, key=lambda n: quality_by_name[n]["score"], reverse=True)
        order.extend(remain_sorted)
    else:
        # 未给优先级：按质量分降序
        order = sorted(dfs.keys(), key=lambda n: quality_by_name[n]["score"], reverse=True)

    # 选主源：满足“覆盖度>0.9 且 滞后<=容忍”的最高优先；否则直接取分数最高
    primary = None

    if prefer_order:
        # 如果指定了优先顺序，优先选择指定顺序中的第一个可用源
        for n in prefer_order:
            if n in dfs:
                q = quality_by_name[n]
                # 只要覆盖度不是极低（>0.5）且不是严重滞后，就选择
                if q["coverage"] > 0.5 and q["lag_days"] <= freshness_tolerance_days * 2:
                    primary = n
                    break

    # 如果按优先顺序没找到合适的，再按质量分选择
    if primary is None:
        for n in order:
            q = quality_by_name[n]
            if q["coverage"] >= 0.9 and q["lag_days"] <= freshness_tolerance_days:
                primary = n
                break

    # 最后的兜底：选择第一个
    if primary is None:
        primary = order[0]

    merged = dfs[primary].copy()
    conflicts: List[Dict] = []
    fallback_used = 0

    # 合并流程：从高优先到低优先，逐日检查缺失/冲突
    for name in order:
        if name == primary:
            continue
        src = dfs[name]
        # 逐日处理
        for dt in sessions:
            row_m = merged.loc[dt]
            row_s = src.loc[dt]

            # 源当天无数据，跳过
            if pd.isna(row_s["close"]):
                continue

            # 若主数据缺失（close 为 NaN），直接用备源填补
            if pd.isna(row_m["close"]):
                merged.loc[dt, ["open", "high", "low", "close", "volume"]] = row_s[["open", "high", "low", "close", "volume"]]
                fallback_used += 1
                continue

            # 冲突判定：close 差异 > 阈值
            base = float(row_m["close"])
            alt = float(row_s["close"])
            if base == 0 or pd.isna(base) or pd.isna(alt):
                continue

            diff_pct = abs(alt - base) / max(1e-12, base)
            if diff_pct > conflict_close_pct:
                # 检查主源当天是否存在明显无效
                invalid_main = bool(
                    (row_m["high"] < row_m["low"])
                    or (row_m["close"] < row_m["low"])
                    or (row_m["close"] > row_m["high"])
                    or (row_m["volume"] < 0)
                )
                # 备源质量是否更高
                better_src = quality_by_name[name]["score"] > quality_by_name[primary]["score"]

                override = False
                reason = f"diff_pct={round(diff_pct*100, 3)}% > {round(conflict_close_pct*100, 2)}%"
                if allow_override_on_invalid and invalid_main and better_src:
                    override = True
                    reason += " 且主源行无效，且备源评分更高 -> 覆盖"
                else:
                    reason += " 保留主源"

                if override:
                    merged.loc[dt, ["open", "high", "low", "close", "volume"]] = row_s[["open", "high", "low", "close", "volume"]]

                conflicts.append({
                    "date": str(dt.date()),
                    "field": "close",
                    "primary": primary,
                    "alt": name,
                    "primary_val": float(base),
                    "alt_val": float(alt),
                    "decision": "override" if override else "keep_primary",
                    "reason": reason,
                })

    logs = {
        "providers_quality": qualities,
        "order": order,
        "primary": primary,
        "fallback_used": fallback_used,
        "conflicts": conflicts,
    }
    return merged, logs
