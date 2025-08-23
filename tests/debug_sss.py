#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本：测试 SSS 策略的信号评估和风控条件
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(project_root))

from backend.core.entry_signals import evaluate_signal
from backend.core.risk_manager import RiskManager

def test_signal_evaluation():
    """测试信号评估函数"""
    print("=== 测试信号评估 ===\n")
    
    # 读取CSV数据
    csv_path = project_root / "data" / "zipline_csv" / "TEST.csv"
    if not csv_path.exists():
        print(f"CSV文件不存在: {csv_path}")
        return False
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 选择2月份的数据进行测试
    test_period = df['2024-02-05':'2024-03-29']
    
    # 模拟30天回看窗口
    lookback = 30
    signal_count = 0
    
    for i in range(lookback, len(test_period)):
        current_date = test_period.index[i]
        
        # 获取历史数据
        hist_start = max(0, i - lookback)
        hist = test_period.iloc[hist_start:i]
        
        if len(hist) < 20:  # 至少需要20天数据
            continue
            
        current_price = float(test_period.iloc[i]['close'])
        
        # 构建payload
        payload = {
            "symbol": "TEST",
            "mode": "breakout",
            "price": current_price,
            "intraday": {
                "first2h_vol_ratio": 0.6,  # 模拟值
                "close_spike_ratio": 0.2    # 模拟值
            },
            "ohlcv": {
                "t": [str(d.date()) for d in hist.index],
                "o": hist["open"].tolist(),
                "h": hist["high"].tolist(),
                "l": hist["low"].tolist(),
                "c": hist["close"].tolist(),
                "v": hist["volume"].tolist()
            }
        }
        
        try:
            result = evaluate_signal(payload)
            if result.get("pass", False):
                signal_count += 1
                print(f"✓ {current_date.date()}: 信号通过 - price={current_price:.2f}")
                print(f"  原因: {result.get('reasons', [])}")
        except Exception as e:
            print(f"✗ {current_date.date()}: 信号评估失败 - {e}")
    
    print(f"\n信号触发次数: {signal_count}/{len(test_period)-lookback}")
    return signal_count > 0

def test_risk_gates():
    """测试风控门评估"""
    print("\n=== 测试风控门 ===\n")
    
    try:
        rm = RiskManager.load_from_config()
        print("风控管理器加载成功")
    except Exception as e:
        print(f"风控管理器加载失败: {e}")
        return False
    
    # 测试不同价格点的风控评估
    test_prices = [10.0, 11.0, 12.0, 15.0, 20.0]
    gates_pass_count = 0
    
    for price in test_prices:
        payload = {
            "symbol": "TEST",
            "sector": "AI",
            "price": price
        }
        
        try:
            result = rm.evaluate_trade_gates(payload)
            passed = result.get("pass", False)
            gates_pass_count += int(passed)
            
            status = "✓ 通过" if passed else "✗ 未通过"
            print(f"{status} - price={price:.2f}")
            
            if not passed:
                # 打印失败原因
                for key, value in result.items():
                    if key != "pass" and not value.get("pass", True):
                        print(f"  {key}: {value}")
                        
        except Exception as e:
            print(f"✗ price={price:.2f} - 评估失败: {e}")
    
    print(f"\n风控通过次数: {gates_pass_count}/{len(test_prices)}")
    return gates_pass_count > 0

def analyze_combined_conditions():
    """分析信号和风控的组合条件"""
    print("\n=== 组合条件分析 ===\n")
    
    csv_path = project_root / "data" / "zipline_csv" / "TEST.csv"
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    test_period = df['2024-02-05':'2024-03-29']
    rm = RiskManager.load_from_config()
    
    lookback = 30
    both_pass_count = 0
    signal_only = 0
    gates_only = 0
    
    for i in range(lookback, len(test_period)):
        current_date = test_period.index[i]
        hist_start = max(0, i - lookback)
        hist = test_period.iloc[hist_start:i]
        
        if len(hist) < 20:
            continue
            
        current_price = float(test_period.iloc[i]['close'])
        
        # 评估信号
        signal_payload = {
            "symbol": "TEST",
            "mode": "breakout",
            "price": current_price,
            "intraday": {"first2h_vol_ratio": 0.6, "close_spike_ratio": 0.2},
            "ohlcv": {
                "t": [str(d.date()) for d in hist.index],
                "o": hist["open"].tolist(),
                "h": hist["high"].tolist(),
                "l": hist["low"].tolist(),
                "c": hist["close"].tolist(),
                "v": hist["volume"].tolist()
            }
        }
        
        # 评估风控
        gates_payload = {
            "symbol": "TEST",
            "sector": "AI",
            "price": current_price
        }
        
        try:
            sig_result = evaluate_signal(signal_payload)
            sig_pass = sig_result.get("pass", False)
        except:
            sig_pass = False
            
        try:
            gates_result = rm.evaluate_trade_gates(gates_payload)
            gates_pass = gates_result.get("pass", False)
        except:
            gates_pass = False
        
        if sig_pass and gates_pass:
            both_pass_count += 1
            print(f"✓✓ {current_date.date()}: 信号和风控都通过 - price={current_price:.2f}")
        elif sig_pass:
            signal_only += 1
            print(f"✓✗ {current_date.date()}: 仅信号通过 - price={current_price:.2f}")
        elif gates_pass:
            gates_only += 1
            # print(f"✗✓ {current_date.date()}: 仅风控通过 - price={current_price:.2f}")
    
    print(f"\n统计结果:")
    print(f"- 两者都通过: {both_pass_count}")
    print(f"- 仅信号通过: {signal_only}")
    print(f"- 仅风控通过: {gates_only}")
    print(f"- 总评估天数: {len(test_period) - lookback}")
    
    return both_pass_count > 0

def suggest_adjustments():
    """建议参数调整"""
    print("\n=== 建议调整 ===\n")
    
    print("如果没有交易产生，可以尝试以下调整：")
    print("\n1. 放宽信号条件 (entry_signals.py):")
    print("   - 降低 breakout 的 margin 参数")
    print("   - 缩短回看窗口 (如从30天改为20天)")
    print("   - 放宽 RSI 等技术指标的阈值")
    
    print("\n2. 放宽风控条件 (risk_manager.py):")
    print("   - 降低最小 RR 要求 (如从2.0改为1.5)")
    print("   - 提高最大 EV 阈值")
    print("   - 放宽板块限制")
    
    print("\n3. 调整策略参数 (algo_sss_strategy.py):")
    print("   - 降低信号预热期要求 (如从20天改为15天)")
    print("   - 使用更宽松的离场条件")
    
    print("\n4. 临时测试建议:")
    print("   - 在 algo_sss_strategy.py 中临时注释掉风控检查")
    print("   - 或者临时降低信号评估的严格程度")
    print("   - 添加更多调试输出以定位问题")

def main():
    print("=" * 60)
    print("SSS 策略诊断工具")
    print("=" * 60)
    
    # 运行各项测试
    signal_ok = test_signal_evaluation()
    gates_ok = test_risk_gates()
    combined_ok = analyze_combined_conditions()
    
    # 提供建议
    suggest_adjustments()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
    if combined_ok:
        print("✓ 应该能产生交易，检查算法实现")
    else:
        print("✗ 条件太严格，需要调整参数")

if __name__ == "__main__":
    main()