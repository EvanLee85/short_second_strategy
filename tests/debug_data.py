#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试脚本：检查CSV数据并分析为什么没有触发交易
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 读取生成的CSV数据
csv_path = Path("data/zipline_csv/TEST.csv")
if not csv_path.exists():
    print(f"CSV文件不存在: {csv_path}")
    exit(1)

df = pd.read_csv(csv_path)
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

print("=== 数据概览 ===")
print(f"数据范围: {df.index[0]} 到 {df.index[-1]}")
print(f"数据条数: {len(df)}")
print(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
print(f"价格变化: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
print()

# 计算20日滚动最高价
lookback = 20
margin = 0.005
df['high_20'] = df['high'].rolling(window=lookback).max()
df['threshold'] = df['high_20'].shift(1) * (1 + margin)  # 前一日的20日高点 * (1+margin)
df['signal'] = df['close'] >= df['threshold']

print("=== 突破分析 ===")
print(f"突破阈值 margin: {margin}")
print(f"回看窗口: {lookback} 天")
print()

# 查看2月份的数据（回测期间）
feb_march = df['2024-02-01':'2024-03-29'].copy()
print(f"回测期间数据: {len(feb_march)} 天")
print(f"回测期间突破信号数: {feb_march['signal'].sum()}")

if feb_march['signal'].sum() > 0:
    print("\n=== 突破日期 ===")
    breakout_dates = feb_march[feb_march['signal']].index
    for date in breakout_dates:
        row = feb_march.loc[date]
        print(f"{date.date()}: close={row['close']:.2f}, high_20={row['high_20']:.2f}, threshold={row['threshold']:.2f}")
else:
    print("\n=== 为什么没有突破？===")
    # 分析价格趋势
    feb_march['daily_return'] = feb_march['close'].pct_change()
    print(f"期间平均日收益率: {feb_march['daily_return'].mean() * 100:.4f}%")
    print(f"期间最大日涨幅: {feb_march['daily_return'].max() * 100:.2f}%")
    
    # 检查最接近突破的几天
    feb_march['distance_to_break'] = (feb_march['threshold'] - feb_march['close']) / feb_march['close']
    closest = feb_march.nsmallest(3, 'distance_to_break')[['close', 'high_20', 'threshold', 'distance_to_break']]
    print("\n最接近突破的3天:")
    for idx, row in closest.iterrows():
        print(f"{idx.date()}: close={row['close']:.2f}, 距离突破={row['distance_to_break']*100:.2f}%")

print("\n=== 建议 ===")
print("如果没有触发交易，可以尝试:")
print("1. 降低 margin 参数（比如从 0.005 改为 0.001 或 0）")
print("2. 缩短 lookback 窗口（比如从 20 改为 10）")
print("3. 修改数据生成逻辑，让价格有更明显的上涨趋势")