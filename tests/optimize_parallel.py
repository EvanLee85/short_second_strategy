#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
并行参数优化脚本 - 使用多进程加速参数搜索
更快速地找到最佳参数组合
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
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Any
import multiprocessing as mp

# 项目路径设置
PROJ = pathlib.Path(__file__).resolve().parents[1] if "__file__" in globals() else pathlib.Path.cwd()
ZIPLINE_ROOT = PROJ / "var" / "zipline"
CSV_DIR = PROJ / "data" / "zipline_csv"
RESULTS_DIR = PROJ / "var" / "optimization_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 简化的参数网格（快速测试）
QUICK_PARAM_GRID = {
    "lookback": [10, 15, 20],
    "position_size": [0.15, 0.20, 0.25],
    "max_hold_days": [5, 8, 10],
    "take_profit": [3.0, 5.0, 7.0],
    "stop_loss": [2.0, 3.0],
    "breakout_threshold": [0.98, 0.99, 1.00],
}

# 完整参数网格
FULL_PARAM_GRID = {
    "lookback": [10, 12, 15, 18, 20, 25],
    "position_size": [0.10, 0.15, 0.20, 0.25, 0.30],
    "max_hold_days": [5, 7, 10, 12, 15],
    "take_profit": [2.0, 3.0, 5.0, 7.0, 10.0],
    "stop_loss": [1.5, 2.0, 3.0, 5.0],
    "breakout_threshold": [0.97, 0.98, 0.99, 1.00, 1.01],
    "ma_exit_ratio": [0.96, 0.97, 0.98, 0.99],
}

def create_strategy_code(params: Dict[str, Any]) -> str:
    """生成策略代码"""
    
    # 设置默认值
    params_with_defaults = {
        "lookback": params.get("lookback", 20),
        "position_size": params.get("position_size", 0.20),
        "max_hold_days": params.get("max_hold_days", 10),
        "take_profit": params.get("take_profit", 5.0),
        "stop_loss": params.get("stop_loss", 3.0),
        "breakout_threshold": params.get("breakout_threshold", 0.99),
        "ma_exit_ratio": params.get("ma_exit_ratio", 0.98),
    }
    
    return f'''# -*- coding: utf-8 -*-
from zipline.api import *
from zipline.finance.commission import PerDollar
from zipline.finance.slippage import FixedSlippage
import pandas as pd

def initialize(context):
    context.asset = symbol("TEST")
    context.lookback = {params_with_defaults['lookback']}
    context.position_size = {params_with_defaults['position_size']}
    context.max_hold_days = {params_with_defaults['max_hold_days']}
    context.take_profit = {params_with_defaults['take_profit']}
    context.stop_loss = {params_with_defaults['stop_loss']}
    context.breakout_threshold = {params_with_defaults['breakout_threshold']}
    context.ma_exit_ratio = {params_with_defaults['ma_exit_ratio']}
    
    context.in_position = False
    context.hold_days = 0
    context.warmup_days = 0
    context.entry_price = None
    
    set_commission(PerDollar(cost=0.0005))
    set_slippage(FixedSlippage(spread=0.0005))
    
    schedule_function(trade, date_rules.every_day(), time_rules.market_open(minutes=30))

def trade(context, data):
    asset = context.asset
    if not data.can_trade(asset):
        return
    
    context.warmup_days += 1
    price = float(data.current(asset, "close"))
    
    # 获取历史数据
    lookback = min(context.lookback, context.warmup_days)
    if lookback < 5:
        record(price=price, in_pos=0)
        return
    
    try:
        hist = data.history(asset, ["high", "low", "close", "volume"], lookback, "1d")
    except:
        record(price=price, in_pos=0)
        return
    
    # 入场信号：突破检测
    if not context.in_position and context.warmup_days >= 10:
        recent_high = hist['high'].max()
        if price >= recent_high * context.breakout_threshold:
            order_target_percent(asset, context.position_size)
            context.in_position = True
            context.hold_days = 0
            context.entry_price = price
    
    # 出场逻辑
    elif context.in_position:
        context.hold_days += 1
        pnl_pct = (price / context.entry_price - 1) * 100 if context.entry_price else 0
        
        exit = False
        if pnl_pct >= context.take_profit:  # 止盈
            exit = True
        elif pnl_pct <= -context.stop_loss:  # 止损
            exit = True
        elif context.hold_days >= context.max_hold_days:  # 时间退出
            exit = True
        elif len(hist) >= 10:  # MA退出
            ma10 = hist["close"].tail(10).mean()
            if price < ma10 * context.ma_exit_ratio:
                exit = True
        
        if exit:
            order_target_percent(asset, 0.0)
            context.in_position = False
            context.entry_price = None
    
    record(price=price, in_pos=int(context.in_position))

def handle_data(context, data):
    pass
'''

def run_single_backtest(params: Dict[str, Any], worker_id: int) -> Dict[str, Any]:
    """运行单个回测（供并行执行）"""
    
    # 为每个worker创建独立的文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    algo_file = PROJ / "var" / f"algo_opt_{worker_id}_{timestamp}.py"
    out_pkl = PROJ / "var" / f"perf_opt_{worker_id}_{timestamp}.pkl"
    
    try:
        # 生成策略文件
        strategy_code = create_strategy_code(params)
        with open(algo_file, 'w', encoding='utf-8') as f:
            f.write(strategy_code)
        
        # 设置环境
        env = os.environ.copy()
        env["ZIPLINE_ROOT"] = str(ZIPLINE_ROOT)
        env["CSVDIR"] = str(CSV_DIR)
        env["PYTHONPATH"] = f"{PROJ}:{env.get('PYTHONPATH','')}"
        
        # 运行回测
        args = [
            sys.executable, "-m", "zipline", "run",
            "-f", str(algo_file),
            "-b", "sss_csv",
            "--start", "2024-02-05",
            "--end", "2024-03-29",
            "--capital-base", "100000",
            "--data-frequency", "daily",
            "--no-benchmark",
            "-o", str(out_pkl),
        ]
        
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"success": False, "params": params, "error": "Backtest failed"}
        
        # 读取结果
        perf = pd.read_pickle(out_pkl)
        
        # 计算指标
        total_return = (perf['portfolio_value'].iloc[-1] / 100000 - 1) * 100
        returns = perf['returns']
        
        # 夏普比率
        if returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe = 0
        
        # 最大回撤
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 交易次数
        n_tx = sum(len(x) for x in perf.get("transactions", []))
        
        return {
            "success": True,
            "params": params,
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": round(max_drawdown, 2),
            "n_transactions": n_tx,
            "final_value": round(perf['portfolio_value'].iloc[-1], 2)
        }
        
    except Exception as e:
        return {"success": False, "params": params, "error": str(e)}
    
    finally:
        # 清理临时文件
        if algo_file.exists():
            algo_file.unlink()
        if out_pkl.exists():
            out_pkl.unlink()

def optimize_parallel(param_grid: Dict, max_workers: int = None):
    """并行优化参数"""
    
    if max_workers is None:
        max_workers = min(mp.cpu_count() - 1, 4)  # 最多使用4个进程
    
    print(f"使用 {max_workers} 个进程进行并行优化")
    
    # 生成所有参数组合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_combinations = list(product(*param_values))
    
    # 转换为参数字典列表
    param_list = [dict(zip(param_names, combo)) for combo in all_combinations]
    
    print(f"总共需要测试 {len(param_list)} 种参数组合")
    print("开始并行回测...\n")
    
    results = []
    successful = 0
    failed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_params = {
            executor.submit(run_single_backtest, params, i): params 
            for i, params in enumerate(param_list)
        }
        
        # 收集结果
        for future in as_completed(future_to_params):
            try:
                result = future.result(timeout=60)
                if result["success"]:
                    results.append(result)
                    successful += 1
                    print(f"✓ [{successful + failed}/{len(param_list)}] "
                          f"收益: {result['total_return']:.1f}%, "
                          f"夏普: {result['sharpe_ratio']:.2f}, "
                          f"回撤: {result['max_drawdown']:.1f}%")
                else:
                    failed += 1
                    print(f"✗ [{successful + failed}/{len(param_list)}] 失败: {result.get('error', 'Unknown')}")
            except Exception as e:
                failed += 1
                print(f"✗ [{successful + failed}/{len(param_list)}] 异常: {e}")
    
    print(f"\n完成！成功: {successful}, 失败: {failed}")
    return results

def analyze_and_save_results(results: List[Dict]):
    """分析并保存优化结果"""
    
    if not results:
        print("没有成功的回测结果")
        return None
    
    # 转换为DataFrame
    df = pd.DataFrame(results)
    
    # 添加综合评分
    df['score'] = (
        df['total_return'] * 0.4 +          # 40% 权重给收益
        df['sharpe_ratio'] * 10 * 0.3 +     # 30% 权重给夏普
        (-df['max_drawdown']) * 0.3         # 30% 权重给回撤控制
    )
    
    # 保存完整结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"optimization_results_{timestamp}.csv"
    df.to_csv(results_file, index=False)
    
    print("\n" + "=" * 70)
    print("📊 优化结果分析")
    print("=" * 70)
    
    # 显示TOP 5
    print("\n🏆 收益率 TOP 5:")
    print("-" * 50)
    top_return = df.nlargest(5, 'total_return')
    for i, row in enumerate(top_return.iterrows(), 1):
        idx, data = row
        print(f"{i}. 收益率: {data['total_return']:.2f}%, "
              f"夏普: {data['sharpe_ratio']:.2f}, "
              f"回撤: {data['max_drawdown']:.2f}%, "
              f"交易: {data['n_transactions']}次")
        params_str = ', '.join([f"{k}={v}" for k, v in data['params'].items()])
        print(f"   参数: {params_str}")
    
    print("\n📈 夏普比率 TOP 5:")
    print("-" * 50)
    top_sharpe = df.nlargest(5, 'sharpe_ratio')
    for i, row in enumerate(top_sharpe.iterrows(), 1):
        idx, data = row
        print(f"{i}. 夏普: {data['sharpe_ratio']:.2f}, "
              f"收益率: {data['total_return']:.2f}%, "
              f"回撤: {data['max_drawdown']:.2f}%")
    
    print("\n💎 综合评分最佳:")
    print("-" * 50)
    best = df.nlargest(1, 'score').iloc[0]
    print(f"综合评分: {best['score']:.2f}")
    print(f"收益率: {best['total_return']:.2f}%")
    print(f"夏普比率: {best['sharpe_ratio']:.2f}")
    print(f"最大回撤: {best['max_drawdown']:.2f}%")
    print(f"交易次数: {best['n_transactions']}")
    print(f"最终价值: ${best['final_value']:,.2f}")
    
    print("\n🎯 最佳参数配置:")
    print("-" * 50)
    for key, value in best['params'].items():
        print(f"  {key}: {value}")
    
    # 保存最佳参数
    best_params_file = RESULTS_DIR / f"best_params_{timestamp}.json"
    with open(best_params_file, 'w') as f:
        json.dump({
            "params": best['params'],
            "metrics": {
                "total_return": best['total_return'],
                "sharpe_ratio": best['sharpe_ratio'],
                "max_drawdown": best['max_drawdown'],
                "n_transactions": int(best['n_transactions']),
                "final_value": best['final_value'],
                "score": best['score']
            },
            "timestamp": timestamp
        }, f, indent=2)
    
    print(f"\n✅ 结果已保存:")
    print(f"  - 完整结果: {results_file}")
    print(f"  - 最佳参数: {best_params_file}")
    
    # 生成最佳策略文件
    generate_best_strategy(best['params'])
    
    return best

def generate_best_strategy(best_params: Dict):
    """生成使用最佳参数的策略文件"""
    
    strategy_file = PROJ / "backend" / "zipline" / "algo_sss_optimized.py"
    
    code = f'''# -*- coding: utf-8 -*-
"""
优化后的SSS策略 - 使用参数优化找到的最佳配置
生成时间: {datetime.now()}
最佳参数: {json.dumps(best_params, indent=2)}
"""

from zipline.api import (
    order_target_percent, record, symbol, set_commission, set_slippage,
    schedule_function, date_rules, time_rules, get_datetime
)
from zipline.finance.commission import PerDollar
from zipline.finance.slippage import FixedSlippage
import pandas as pd

# 优化后的参数
OPTIMIZED_PARAMS = {json.dumps(best_params, indent=4)}

def initialize(context):
    context.asset = symbol("TEST")
    
    # 使用优化后的参数
    params = OPTIMIZED_PARAMS
    context.lookback = params.get('lookback', 20)
    context.position_size = params.get('position_size', 0.20)
    context.max_hold_days = params.get('max_hold_days', 10)
    context.take_profit = params.get('take_profit', 5.0)
    context.stop_loss = params.get('stop_loss', 3.0)
    context.breakout_threshold = params.get('breakout_threshold', 0.99)
    context.ma_exit_ratio = params.get('ma_exit_ratio', 0.98)
    
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

def rebalance(context, data):
    """使用优化参数的交易逻辑"""
    asset = context.asset
    if not data.can_trade(asset):
        return
    
    context.warmup_days += 1
    price = float(data.current(asset, "close"))
    
    # 获取历史数据
    lookback = min(context.lookback, context.warmup_days)
    if lookback < 5:
        record(price=price, in_pos=0)
        return
    
    try:
        hist = data.history(asset, ["high", "low", "close", "volume"], lookback, "1d")
    except:
        record(price=price, in_pos=0)
        return
    
    # 入场信号
    if not context.in_position and context.warmup_days >= 10:
        recent_high = hist['high'].max()
        if price >= recent_high * context.breakout_threshold:
            order_target_percent(asset, context.position_size)
            context.in_position = True
            context.hold_days = 0
            context.entry_price = price
            print(f"{{get_datetime()}}: BUY at {{price:.2f}}")
    
    # 出场逻辑
    elif context.in_position:
        context.hold_days += 1
        pnl_pct = (price / context.entry_price - 1) * 100 if context.entry_price else 0
        
        exit_signal = False
        exit_reason = ""
        
        if pnl_pct >= context.take_profit:
            exit_signal = True
            exit_reason = f"Take profit at {{pnl_pct:.1f}}%"
        elif pnl_pct <= -context.stop_loss:
            exit_signal = True
            exit_reason = f"Stop loss at {{pnl_pct:.1f}}%"
        elif context.hold_days >= context.max_hold_days:
            exit_signal = True
            exit_reason = "Max holding days"
        elif len(hist) >= 10:
            ma10 = hist["close"].tail(10).mean()
            if price < ma10 * context.ma_exit_ratio:
                exit_signal = True
                exit_reason = "Below MA10"
        
        if exit_signal:
            order_target_percent(asset, 0.0)
            context.in_position = False
            context.entry_price = None
            print(f"{{get_datetime()}}: SELL at {{price:.2f}} - {{exit_reason}}")
    
    record(price=price, in_pos=int(context.in_position))

def handle_data(context, data):
    pass
'''
    
    with open(strategy_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"\n📝 已生成优化策略文件: {strategy_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='策略参数并行优化工具')
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                       help='优化模式: quick(快速) 或 full(完整)')
    parser.add_argument('--workers', type=int, default=None,
                       help='并行进程数（默认为CPU核心数-1，最多4个）')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 策略参数优化工具")
    print("=" * 70)
    
    # 选择参数网格
    if args.mode == 'quick':
        param_grid = QUICK_PARAM_GRID
        print("模式: 快速优化")
    else:
        param_grid = FULL_PARAM_GRID
        print("模式: 完整优化")
    
    # 显示参数空间
    total_combinations = 1
    for param, values in param_grid.items():
        total_combinations *= len(values)
        print(f"  {param}: {values}")
    
    print(f"\n总组合数: {total_combinations}")
    
    # 确认继续
    if total_combinations > 100:
        response = input("\n组合数较多，可能需要一些时间。继续？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            return
    
    # 开始优化
    start_time = datetime.now()
    results = optimize_parallel(param_grid, args.workers)
    end_time = datetime.now()
    
    # 分析结果
    best = analyze_and_save_results(results)
    
    # 显示耗时
    duration = (end_time - start_time).total_seconds()
    print(f"\n⏱️ 总耗时: {duration:.1f}秒")
    print(f"平均每个回测: {duration/len(results):.1f}秒" if results else "")
    
    print("\n✨ 优化完成！")

if __name__ == "__main__":
    main()