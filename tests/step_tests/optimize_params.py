#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
串行参数优化脚本：通过网格搜索找到最佳的策略参数组合
"""

import os
import sys
import json
import subprocess
import pathlib
import pandas as pd
import numpy as np
from itertools import product
from datetime import datetime
import pickle
import shutil
from typing import Dict, List, Tuple, Any

# 项目路径设置
PROJ = pathlib.Path(__file__).resolve().parents[1] if "__file__" in globals() else pathlib.Path.cwd()
ZIPLINE_ROOT = PROJ / "var" / "zipline"
CSV_DIR = PROJ / "data" / "zipline_csv"
ALGO_TEMPLATE = PROJ / "backend" / "zipline" / "algo_sss_strategy_relaxed.py"
ALGO_OPTIMIZED = PROJ / "backend" / "zipline" / "algo_sss_optimized.py"
RESULTS_DIR = PROJ / "var" / "optimization_results"

# 创建结果目录
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 参数搜索空间定义
PARAM_GRID = {
    # 信号参数
    "lookback": [10, 15, 20, 25],                    # 回看窗口
    "warmup_days": [10, 15, 20],                     # 预热期
    "vol_ratio": [0.2, 0.3, 0.4, 0.5],              # 成交量比率阈值
    "spike_ratio": [0.05, 0.1, 0.15, 0.2],          # 价格spike阈值
    
    # 仓位和风控参数
    "position_size": [0.15, 0.20, 0.25, 0.30],      # 仓位大小
    "max_hold_days": [5, 8, 10, 12],                # 最大持仓天数
    "take_profit": [3.0, 5.0, 7.0, 10.0],           # 止盈百分比
    "stop_loss": [2.0, 3.0, 5.0],                   # 止损百分比
    
    # 突破参数
    "breakout_threshold": [0.98, 0.99, 1.00, 1.01], # 突破阈值（相对于历史高点）
    "ma_exit_ratio": [0.97, 0.98, 0.99],            # MA离场比率
}

def generate_strategy_file(params: Dict[str, Any]) -> str:
    """根据参数生成策略文件"""
    
    strategy_code = f'''# -*- coding: utf-8 -*-
"""
自动生成的优化策略 - 参数组合测试
Generated at: {datetime.now()}
Parameters: {json.dumps(params, indent=2)}
"""
from zipline.api import (
    order_target_percent, record, symbol, set_commission, set_slippage,
    schedule_function, date_rules, time_rules, get_datetime
)
from zipline.finance.commission import PerDollar
from zipline.finance.slippage import FixedSlippage
import pandas as pd
import numpy as np

def initialize(context):
    context.asset = symbol("TEST")
    context.lookback = {params['lookback']}
    context.warmup_days_required = {params['warmup_days']}
    context.max_hold_days = {params['max_hold_days']}
    context.position_size = {params['position_size']}
    context.take_profit = {params['take_profit']}
    context.stop_loss = {params['stop_loss']}
    context.breakout_threshold = {params['breakout_threshold']}
    context.ma_exit_ratio = {params['ma_exit_ratio']}
    context.vol_ratio = {params['vol_ratio']}
    context.spike_ratio = {params['spike_ratio']}
    
    context.in_position = False
    context.hold_days = 0
    context.warmup_days = 0
    context.entry_price = None
    
    set_commission(PerDollar(cost=0.0005))
    set_slippage(FixedSlippage(spread=0.0005))
    
    schedule_function(
        rebalance,
        date_rules.every_day(),
        time_rules.market_open(minutes=30)
    )

def simple_breakout_check(hist_df, price, lookback, threshold):
    if len(hist_df) < lookback:
        return False
    recent_high = hist_df['high'].tail(lookback).max()
    return price >= recent_high * threshold

def rebalance(context, data):
    asset = context.asset
    if not data.can_trade(asset):
        return
    
    context.warmup_days += 1
    price = float(data.current(asset, "close"))
    
    try:
        actual_lookback = min(context.lookback, context.warmup_days)
        if actual_lookback < 5:
            record(price=price, in_pos=0)
            return
        
        hist = data.history(asset, ["open", "high", "low", "close", "volume"],
                           actual_lookback, "1d").dropna()
        
        if len(hist) < 5:
            record(price=price, in_pos=0)
            return
    except:
        record(price=price, in_pos=0)
        return
    
    # 信号检测
    sig_pass = False
    if context.warmup_days >= context.warmup_days_required:
        sig_pass = simple_breakout_check(hist, price, 
                                        min(context.lookback, len(hist)), 
                                        context.breakout_threshold)
        
        # 额外的成交量检查（简化版）
        if sig_pass and len(hist) > 1:
            vol_ratio = hist['volume'].iloc[-1] / hist['volume'].mean()
            if vol_ratio < context.vol_ratio:
                sig_pass = False
    
    # 开仓逻辑
    if (not context.in_position) and sig_pass:
        order_target_percent(asset, context.position_size)
        context.in_position = True
        context.hold_days = 0
        context.entry_price = price
    
    # 平仓逻辑
    elif context.in_position:
        context.hold_days += 1
        
        if context.entry_price:
            pnl_pct = (price / context.entry_price - 1) * 100
        else:
            pnl_pct = 0
        
        exit_signal = False
        
        # 止盈
        if pnl_pct >= context.take_profit:
            exit_signal = True
        # 止损
        elif pnl_pct <= -context.stop_loss:
            exit_signal = True
        # 时间止损
        elif context.hold_days >= context.max_hold_days:
            exit_signal = True
        # MA离场
        elif len(hist) >= 10:
            ma10 = float(hist["close"].tail(10).mean())
            if price < ma10 * context.ma_exit_ratio:
                exit_signal = True
        
        if exit_signal:
            order_target_percent(asset, 0.0)
            context.in_position = False
            context.hold_days = 0
            context.entry_price = None
    
    record(price=price, in_pos=int(context.in_position))

def handle_data(context, data):
    pass
'''
    
    # 保存策略文件
    with open(ALGO_OPTIMIZED, 'w', encoding='utf-8') as f:
        f.write(strategy_code)
    
    return str(ALGO_OPTIMIZED)

def run_backtest(params: Dict[str, Any]) -> Dict[str, Any]:
    """运行单次回测"""
    
    # 生成策略文件
    algo_file = generate_strategy_file(params)
    
    # 设置输出文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_pkl = ZIPLINE_ROOT / f"opt_perf_{timestamp}.pkl"
    
    # 环境变量
    env = os.environ.copy()
    env["ZIPLINE_ROOT"] = str(ZIPLINE_ROOT)
    env["CSVDIR"] = str(CSV_DIR)
    env["PYTHONPATH"] = f"{PROJ}:{env.get('PYTHONPATH','')}"
    
    # 运行回测命令
    args = [
        "zipline", "run",
        "-f", algo_file,
        "-b", "sss_csv",
        "--start", "2024-02-05",
        "--end", "2024-03-29",
        "--capital-base", "100000",
        "--data-frequency", "daily",
        "--no-benchmark",
        "-o", str(out_pkl),
    ]
    
    try:
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"✗ Backtest failed for params: {params}")
            return {"success": False, "error": result.stderr}
        
        # 读取结果
        perf = pd.read_pickle(out_pkl)
        
        # 计算关键指标
        returns = perf['returns']
        total_return = (perf['portfolio_value'].iloc[-1] / 100000 - 1) * 100
        
        # 计算夏普比率
        if returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe = 0
        
        # 计算最大回撤
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 交易统计
        n_transactions = sum(len(x) for x in perf.get("transactions", []))
        
        # 清理临时文件
        if out_pkl.exists():
            out_pkl.unlink()
        
        return {
            "success": True,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "n_transactions": n_transactions,
            "final_value": perf['portfolio_value'].iloc[-1],
            "params": params
        }
        
    except subprocess.TimeoutExpired:
        print(f"✗ Backtest timeout for params: {params}")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"✗ Error in backtest: {e}")
        return {"success": False, "error": str(e)}

def optimize_parameters():
    """执行参数优化"""
    
    print("=" * 60)
    print("策略参数优化开始")
    print("=" * 60)
    
    # 生成所有参数组合
    param_names = list(PARAM_GRID.keys())
    param_values = list(PARAM_GRID.values())
    all_combinations = list(product(*param_values))
    
    total_combinations = len(all_combinations)
    print(f"总共需要测试 {total_combinations} 种参数组合")
    print("这可能需要一些时间...\n")
    
    # 存储所有结果
    results = []
    
    # 测试每种组合
    for i, combination in enumerate(all_combinations, 1):
        params = dict(zip(param_names, combination))
        
        print(f"[{i}/{total_combinations}] 测试参数组合...")
        
        result = run_backtest(params)
        
        if result["success"]:
            results.append(result)
            print(f"  ✓ 收益率: {result['total_return']:.2f}%, "
                  f"夏普: {result['sharpe_ratio']:.2f}, "
                  f"最大回撤: {result['max_drawdown']:.2f}%, "
                  f"交易次数: {result['n_transactions']}")
        else:
            print(f"  ✗ 失败: {result.get('error', 'Unknown error')}")
        
        # 每10次保存一次中间结果
        if i % 10 == 0:
            save_intermediate_results(results)
    
    return results

def save_intermediate_results(results: List[Dict]):
    """保存中间结果"""
    if results:
        df = pd.DataFrame(results)
        df.to_csv(RESULTS_DIR / "intermediate_results.csv", index=False)

def analyze_results(results: List[Dict]):
    """分析优化结果"""
    
    if not results:
        print("没有成功的回测结果")
        return
    
    # 转换为DataFrame
    df = pd.DataFrame(results)
    
    # 保存完整结果
    df.to_csv(RESULTS_DIR / "optimization_results.csv", index=False)
    
    print("\n" + "=" * 60)
    print("优化结果分析")
    print("=" * 60)
    
    # 按不同指标排序并显示前5名
    print("\n📈 按总收益率排序（前5名）:")
    top_return = df.nlargest(5, 'total_return')
    for idx, row in top_return.iterrows():
        print(f"\n收益率: {row['total_return']:.2f}%")
        print(f"夏普比率: {row['sharpe_ratio']:.2f}")
        print(f"最大回撤: {row['max_drawdown']:.2f}%")
        print(f"交易次数: {row['n_transactions']}")
        print(f"参数: {json.dumps(row['params'], indent=2)}")
        print("-" * 40)
    
    print("\n📊 按夏普比率排序（前5名）:")
    top_sharpe = df.nlargest(5, 'sharpe_ratio')
    for idx, row in top_sharpe.head(3).iterrows():
        print(f"\n夏普比率: {row['sharpe_ratio']:.2f}")
        print(f"收益率: {row['total_return']:.2f}%")
        print(f"参数: {json.dumps(row['params'], indent=2)}")
    
    print("\n💎 综合评分最佳（考虑收益、夏普、回撤）:")
    # 计算综合评分
    df['score'] = (
        df['total_return'] * 0.4 +  # 40% 权重给收益
        df['sharpe_ratio'] * 10 * 0.3 +  # 30% 权重给夏普
        (-df['max_drawdown']) * 0.3  # 30% 权重给回撤控制
    )
    
    best_overall = df.nlargest(1, 'score').iloc[0]
    print(f"\n最佳参数组合:")
    print(f"综合评分: {best_overall['score']:.2f}")
    print(f"收益率: {best_overall['total_return']:.2f}%")
    print(f"夏普比率: {best_overall['sharpe_ratio']:.2f}")
    print(f"最大回撤: {best_overall['max_drawdown']:.2f}%")
    print(f"交易次数: {best_overall['n_transactions']}")
    print(f"\n最佳参数配置:")
    print(json.dumps(best_overall['params'], indent=2))
    
    # 保存最佳参数
    with open(RESULTS_DIR / "best_params.json", 'w') as f:
        json.dump({
            "params": best_overall['params'],
            "metrics": {
                "total_return": best_overall['total_return'],
                "sharpe_ratio": best_overall['sharpe_ratio'],
                "max_drawdown": best_overall['max_drawdown'],
                "n_transactions": int(best_overall['n_transactions']),
                "score": best_overall['score']
            }
        }, f, indent=2)
    
    print(f"\n✅ 结果已保存到: {RESULTS_DIR}")
    print(f"  - 完整结果: optimization_results.csv")
    print(f"  - 最佳参数: best_params.json")
    
    return best_overall

def quick_test():
    """快速测试模式 - 只测试少量参数组合"""
    
    # 简化的参数网格
    quick_grid = {
        "lookback": [15, 20],
        "warmup_days": [10, 15],
        "vol_ratio": [0.3, 0.4],
        "spike_ratio": [0.1, 0.15],
        "position_size": [0.20, 0.25],
        "max_hold_days": [8, 10],
        "take_profit": [5.0, 7.0],
        "stop_loss": [3.0],
        "breakout_threshold": [0.99, 1.00],
        "ma_exit_ratio": [0.98],
    }
    
    global PARAM_GRID
    PARAM_GRID = quick_grid
    
    print("🚀 快速测试模式 - 使用简化参数集")
    results = optimize_parameters()
    best = analyze_results(results)
    return best

def main():
    """主函数"""
    
    import argparse
    parser = argparse.ArgumentParser(description='策略参数优化工具')
    parser.add_argument('--quick', action='store_true', help='快速测试模式（少量参数）')
    parser.add_argument('--full', action='store_true', help='完整优化模式（所有参数）')
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    elif args.full:
        results = optimize_parameters()
        analyze_results(results)
    else:
        print("请选择运行模式:")
        print("  --quick  快速测试（约测试32种组合）")
        print("  --full   完整优化（约测试数百种组合）")
        print("\n推荐先运行: python optimize_params.py --quick")

if __name__ == "__main__":
    main()