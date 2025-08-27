# -*- coding: utf-8 -*-
"""
多源合并与回退 自测脚本 - 完全修正版
---------------------------------
修正的关键问题：
1. akshare(主源) 在第3根缺失，tushare(备源) 完整 → 触发回填
2. akshare 在第5根抬高3%，tushare 正常 → 触发冲突检测
3. 修正所有输出信息的对应关系
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# 项目根目录加入 PYTHONPATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from backend.data.merge import merge_ohlcv
from backend.data.normalize import get_sessions_index


def build_df(sessions, base_price=10.0, drift=0.01, miss_index=None, bump_idx=None, bump_pct=0.02):
    """构造简单等差随机游走数据，支持指定一日缺失、某日抬高 close 以制造冲突。"""
    n = len(sessions)
    # 构造递增价格序列
    close = base_price * (1 + drift) ** np.arange(n)
    
    # 在指定位置抬高价格以制造冲突
    if bump_idx is not None and 0 <= bump_idx < n:
        close[bump_idx] *= (1 + bump_pct)

    # 生成 OHLC
    open_ = close * (1 - 0.002)
    high = close * (1 + 0.003)
    low = close * (1 - 0.003)
    vol = np.full(n, 1_000.0)

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": vol,
    }, index=sessions)

    # 在指定位置设置缺失值
    if miss_index is not None and 0 <= miss_index < n:
        df.iloc[miss_index, :] = np.nan

    return df


def main():
    print("开始多源合并测试...")
    
    start, end = "2024-01-02", "2024-01-12"
    sessions = get_sessions_index(start, end, calendar_name="XSHG")
    
    print(f"交易会话数: {len(sessions)}")
    print(f"会话范围: {sessions[0]} 到 {sessions[-1]}")

    # 构造测试数据 - 修正版
    # akshare(主源)：在第3根(索引2)缺失，在第5根(索引4)抬高3%
    df_ak = build_df(sessions, base_price=10.0, drift=0.01, miss_index=2, bump_idx=4, bump_pct=0.03)
    
    # tushare(备源)：完整数据，用于回填akshare缺失的第3根
    df_ts = build_df(sessions, base_price=10.0, drift=0.01, miss_index=None, bump_idx=None)

    # 调试输出：检查构造的数据
    print("\n=== 数据构造验证 ===")
    print("akshare 第3根 (应该为 NaN - 需要回填):")
    if len(df_ak) > 2:
        print(f"  close[2] = {df_ak.iloc[2]['close']}")
    
    print("tushare 第3根价格 (用于回填):")
    if len(df_ts) > 2:
        print(f"  close[2] = {df_ts.iloc[2]['close']:.6f}")
    
    print("akshare 第5根价格 (应该被抬高 - 产生冲突):")
    if len(df_ak) > 4:
        print(f"  close[4] = {df_ak.iloc[4]['close']:.6f}")
    
    print("tushare 第5根价格 (正常):")
    if len(df_ts) > 4:
        print(f"  close[4] = {df_ts.iloc[4]['close']:.6f}")

    # 预期差异计算（第5根的冲突）
    if len(df_ak) > 4 and len(df_ts) > 4:
        ak_close_4 = df_ak.iloc[4]['close']
        ts_close_4 = df_ts.iloc[4]['close']
        if not pd.isna(ak_close_4) and not pd.isna(ts_close_4):
            expected_diff = abs(ak_close_4 - ts_close_4) / ts_close_4
            print(f"预期第5根差异: {expected_diff*100:.3f}%")

    # 执行合并
    print("\n=== 执行合并 ===")
    merged, logs = merge_ohlcv(
        {"akshare": df_ak, "tushare": df_ts},
        start, end,
        calendar_name="XSHG",
        prefer_order=["akshare", "tushare"],
        freshness_tolerance_days=3,
        conflict_close_pct=0.01,  # 1%
        allow_override_on_invalid=True,
    )

    print("合并完成，开始验证结果...")

    # 验证结果
    # 断言 1：主源应为 akshare
    ok_primary = logs.get("primary") == "akshare"
    print(f"主源选择正确: {ok_primary} (实际: {logs.get('primary')})")

    # 断言 2：应该有冲突记录
    conflicts = logs.get("conflicts", [])
    has_conflict = len(conflicts) > 0
    print(f"检测到冲突: {has_conflict} (冲突数: {len(conflicts)})")

    # 断言 3：冲突决策应该是 keep_primary
    kept_primary = any(c.get("decision") == "keep_primary" for c in conflicts)
    print(f"保留主源决策: {kept_primary}")

    # 断言 4：应该有回填使用
    fallback_used = logs.get("fallback_used", 0)
    ok_fallback = fallback_used > 0
    print(f"使用回填: {ok_fallback} (回填次数: {fallback_used})")

    # 综合评估
    all_pass = ok_primary and has_conflict and kept_primary and ok_fallback
    
    print(f"\n=== 测试结果 ===")
    print(("[PASS]" if all_pass else "[FAIL]"), "merge.basic")
    
    if not all_pass:
        print("\n详细诊断信息:")
        print(json.dumps({
            "ok_primary": ok_primary,
            "has_conflict": has_conflict,
            "kept_primary": kept_primary,
            "ok_fallback": ok_fallback,
            "actual_primary": logs.get("primary"),
            "fallback_used": fallback_used,
            "conflicts_count": len(conflicts),
            "providers_quality": logs.get("providers_quality"),
        }, ensure_ascii=False, indent=2))

    # 输出日志概览
    print("\n=== 合并日志概览 ===")
    print(json.dumps({
        "primary": logs.get("primary"),
        "providers_quality": logs.get("providers_quality"),
        "fallback_used": logs.get("fallback_used"),
        "conflicts_count": len(conflicts),
        "conflicts_sample": conflicts[:2],  # 只显示前2个冲突
    }, ensure_ascii=False, indent=2))

    # 输出合并结果样本
    print("\n=== 合并数据样本 ===")
    print("前3行:")
    print(merged.head(3).to_string())
    print("\n后3行:")
    print(merged.tail(3).to_string())
    
    # 特别检查冲突日和回填日
    print("\n=== 关键日期检查 ===")
    if len(sessions) > 4:
        print(f"第5根 ({sessions[4].date()}) - 预期冲突日:")
        print(f"  merged close = {merged.iloc[4]['close']:.6f}")
    
    if len(sessions) > 2:
        print(f"第3根 ({sessions[2].date()}) - 预期回填日:")
        print(f"  akshare close = {df_ak.iloc[2]['close']}")  # 应该是 NaN
        print(f"  tushare close = {df_ts.iloc[2]['close']:.6f}")  # 应该是正常值
        print(f"  merged close = {merged.iloc[2]['close']:.6f}")  # 应该等于tushare的值

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)