# -*- coding: utf-8 -*-
"""
放宽条件版本的SSS策略 - 用于测试交易系统是否正常工作
临时降低信号和风控的严格程度
"""
from zipline.api import (
    order_target_percent, record, symbol, set_commission, set_slippage,
    schedule_function, date_rules, time_rules, get_datetime
)
from zipline.finance.commission import PerDollar
from zipline.finance.slippage import FixedSlippage

import pandas as pd
import numpy as np

# —— 业务逻辑模块 —— #
from backend.core.entry_signals import evaluate_signal
from backend.core.risk_manager import RiskManager

def initialize(context):
    # 与 13-2 的 CSV 文件名一致：TEST.csv -> symbol("TEST")
    context.asset = symbol("TEST")
    context.lookback = 20           # 缩短回看窗口
    context.max_hold_days = 10      # 延长持仓时间
    context.in_position = False
    context.hold_days = 0
    context.warmup_days = 0
    context.entry_price = None      # 记录入场价格

    # 手续费/滑点
    set_commission(PerDollar(cost=0.0005))
    set_slippage(FixedSlippage(spread=0.0005))

    # 预加载风控器
    try:
        context.rm = RiskManager.load_from_config()
        context.use_risk_manager = True
    except:
        print("Warning: RiskManager failed to load, will bypass risk checks")
        context.use_risk_manager = False
    
    # 使用 schedule_function
    schedule_function(
        rebalance,
        date_rules.every_day(),
        time_rules.market_open(minutes=30)
    )

def _build_relaxed_payload(hist_df: pd.DataFrame, price: float) -> dict:
    """构建放宽条件的payload"""
    t = [str(d.date()) for d in hist_df.index]
    o = hist_df["open"].astype(float).tolist()
    h = hist_df["high"].astype(float).tolist()
    l = hist_df["low"].astype(float).tolist()
    c = hist_df["close"].astype(float).tolist()
    v = hist_df["volume"].astype(float).tolist()

    payload = {
        "symbol": "TEST",
        "mode": "breakout",
        "price": float(price),
        # 放宽 intraday 条件
        "intraday": {
            "first2h_vol_ratio": 0.3,  # 降低要求 (原0.6)
            "close_spike_ratio": 0.1   # 降低要求 (原0.2)
        },
        "ohlcv": {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}
    }
    return payload

def simple_breakout_check(hist_df: pd.DataFrame, price: float, lookback: int = 10) -> bool:
    """简单的突破检查 - 作为备用信号"""
    if len(hist_df) < lookback:
        return False
    
    # 计算最近N天的最高价
    recent_high = hist_df['high'].tail(lookback).max()
    
    # 如果当前价格超过最近高点的99%，视为突破
    return price >= recent_high * 0.99

def rebalance(context, data):
    """主要的交易逻辑 - 放宽版本"""
    asset = context.asset
    if not data.can_trade(asset):
        return

    # 增加预热期计数
    context.warmup_days += 1
    
    # 获取当前价格
    price = float(data.current(asset, "close"))
    
    # 安全地获取历史数据
    try:
        actual_lookback = min(context.lookback, context.warmup_days)
        
        # 至少需要5天数据
        if actual_lookback < 5:
            record(price=price, in_pos=0)
            return
        
        hist = data.history(asset, ["open", "high", "low", "close", "volume"],
                           actual_lookback, "1d").dropna()
        
        if len(hist) < 5:
            record(price=price, in_pos=0)
            return
            
    except Exception as e:
        print(f"Warning: Failed to get history data: {e}")
        record(price=price, in_pos=0)
        return

    # —— 1) 信号评估（放宽版） —— #
    sig_pass = False
    
    # 先尝试原始信号评估
    if context.warmup_days >= 15:  # 降低预热期要求
        try:
            sig = evaluate_signal(_build_relaxed_payload(hist, price))
            sig_pass = bool(sig.get("pass", False))
            if sig_pass:
                print(f"{get_datetime()}: Original signal passed at {price:.2f}")
        except Exception as e:
            # print(f"Original signal check failed: {e}")
            pass
    
    # 如果原始信号失败，使用简单突破检查
    if not sig_pass and context.warmup_days >= 10:
        sig_pass = simple_breakout_check(hist, price, lookback=10)
        if sig_pass:
            print(f"{get_datetime()}: Simple breakout signal at {price:.2f}")

    # —— 2) 风控评估（可选） —— #
    gates_pass = True  # 默认通过
    
    if context.use_risk_manager:
        try:
            gates = context.rm.evaluate_trade_gates({
                "symbol": "TEST", 
                "sector": "AI", 
                "price": price
            })
            gates_pass = bool(gates.get("pass", False))
        except:
            gates_pass = True  # 如果风控评估失败，默认通过
    
    # —— 3) 开/平仓逻辑 —— #
    if (not context.in_position) and sig_pass:
        # 即使风控不通过，也可以小仓位尝试
        position_size = 0.20 if gates_pass else 0.10
        
        order_target_percent(asset, position_size)
        context.in_position = True
        context.hold_days = 0
        context.entry_price = price
        
        risk_status = "with risk approval" if gates_pass else "without risk approval"
        print(f"{get_datetime()}: Opening {position_size*100:.0f}% position at {price:.2f} {risk_status}")

    elif context.in_position:
        context.hold_days += 1
        
        # 计算收益率
        if context.entry_price:
            pnl_pct = (price / context.entry_price - 1) * 100
        else:
            pnl_pct = 0
        
        # 离场条件（放宽版）
        exit_signal = False
        exit_reason = ""
        
        # 止盈：收益超过5%
        if pnl_pct >= 5.0:
            exit_signal = True
            exit_reason = f"Take profit at {pnl_pct:.1f}%"
        
        # 止损：亏损超过3%
        elif pnl_pct <= -3.0:
            exit_signal = True
            exit_reason = f"Stop loss at {pnl_pct:.1f}%"
        
        # 时间止损：超过最大持仓天数
        elif context.hold_days >= context.max_hold_days:
            exit_signal = True
            exit_reason = f"Max holding days ({context.max_hold_days})"
        
        # 简单MA离场：价格跌破10日均线
        elif len(hist) >= 10:
            ma10 = float(hist["close"].tail(10).mean())
            if price < ma10 * 0.98:  # 跌破MA10的98%
                exit_signal = True
                exit_reason = "Below MA10"
        
        if exit_signal:
            order_target_percent(asset, 0.0)
            context.in_position = False
            context.hold_days = 0
            print(f"{get_datetime()}: Closing at {price:.2f} - {exit_reason} (PnL: {pnl_pct:.1f}%)")
            context.entry_price = None

    # 记录回测指标
    record(price=price, in_pos=int(context.in_position))

def handle_data(context, data):
    """保留空函数避免冲突"""
    pass