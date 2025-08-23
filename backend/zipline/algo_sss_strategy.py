# -*- coding: utf-8 -*-
from zipline.api import (
    order_target_percent, record, symbol, set_commission, set_slippage,
    schedule_function, date_rules, time_rules, get_datetime
)
from zipline.finance.commission import PerDollar
from zipline.finance.slippage import FixedSlippage

import pandas as pd

# —— 业务逻辑模块 —— #
from backend.core.entry_signals import evaluate_signal
from backend.core.risk_manager import RiskManager

def initialize(context):
    # 与 13-2 的 CSV 文件名一致：TEST.csv -> symbol("TEST")
    context.asset = symbol("TEST")
    context.lookback = 30
    context.max_hold_days = 8       # 简单持仓上限
    context.in_position = False
    context.hold_days = 0
    context.warmup_days = 0         # 添加预热期计数器

    # 手续费/滑点（与风控里假设的大致一致）
    set_commission(PerDollar(cost=0.0005))
    set_slippage(FixedSlippage(spread=0.0005))

    # 预加载风控器
    context.rm = RiskManager.load_from_config()
    
    # 使用 schedule_function 而不是 handle_data，更高效
    schedule_function(
        rebalance,
        date_rules.every_day(),
        time_rules.market_open(minutes=30)
    )

def _build_payload(hist_df: pd.DataFrame, price: float) -> dict:
    """构建信号评估所需的payload"""
    # Zipline 的 history 索引是 DatetimeIndex
    t = [str(d.date()) for d in hist_df.index]
    o = hist_df["open"].astype(float).tolist()
    h = hist_df["high"].astype(float).tolist()
    l = hist_df["low"].astype(float).tolist()
    c = hist_df["close"].astype(float).tolist()
    v = hist_df["volume"].astype(float).tolist()

    payload = {
        "symbol": "TEST",
        "mode": "breakout",
        "price": float(price),  # ★ 用当前价参与"是否突破"的判定
        "intraday": {"first2h_vol_ratio": 0.6, "close_spike_ratio": 0.2},
        "ohlcv": {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}
    }
    return payload

def rebalance(context, data):
    """主要的交易逻辑"""
    asset = context.asset
    if not data.can_trade(asset):
        return

    # 增加预热期计数
    context.warmup_days += 1
    
    # 获取当前价格
    price = float(data.current(asset, "close"))
    
    # 安全地获取历史数据
    try:
        # 根据实际可用数据调整 lookback
        actual_lookback = min(context.lookback, context.warmup_days)
        
        # 至少需要5天数据才开始评估信号
        if actual_lookback < 5:
            record(price=price, in_pos=0)
            return
        
        hist = data.history(asset, ["open", "high", "low", "close", "volume"],
                           actual_lookback, "1d").dropna()
        
        if len(hist) < 5:
            record(price=price, in_pos=0)
            return
            
    except Exception as e:
        # 如果获取历史数据失败，记录并跳过
        print(f"Warning: Failed to get history data: {e}")
        record(price=price, in_pos=0)
        return

    # 信号评估需要足够的数据（至少20天才比较可靠）
    signal_ready = context.warmup_days >= 20
    
    # —— 1) 结构/子型信号 —— #
    sig_pass = False
    if signal_ready:
        try:
            sig = evaluate_signal(_build_payload(hist, price))
            sig_pass = bool(sig.get("pass", False))
        except Exception as e:
            print(f"Warning: Signal evaluation failed: {e}")
            sig_pass = False

    # —— 2) 交易门（RR / EV 等） —— #
    gates_pass = False
    try:
        gates = context.rm.evaluate_trade_gates({
            "symbol": "TEST", 
            "sector": "AI", 
            "price": price
        })
        gates_pass = bool(gates.get("pass", False))
    except Exception as e:
        print(f"Warning: Risk gates evaluation failed: {e}")
        gates_pass = False

    # —— 3) 开/平仓逻辑 —— #
    if (not context.in_position) and sig_pass and gates_pass:
        # 入场：20% 仓位
        order_target_percent(asset, 0.20)
        context.in_position = True
        context.hold_days = 0
        print(f"{get_datetime()}: Opening position at {price:.2f}")

    elif context.in_position:
        context.hold_days += 1

        # 简单离场条件
        exit_signal = False
        exit_reason = ""
        
        # 条件1：价格跌破5日均线
        if len(hist) >= 5:
            ma5 = float(hist["close"].tail(5).mean())
            if price < ma5:
                exit_signal = True
                exit_reason = "Below MA5"
        
        # 条件2：风控门失效
        if not gates_pass:
            exit_signal = True
            exit_reason = "Risk gates failed"
        
        # 条件3：超过最大持仓天数
        if context.hold_days >= context.max_hold_days:
            exit_signal = True
            exit_reason = "Max holding days"
        
        if exit_signal:
            order_target_percent(asset, 0.0)
            context.in_position = False
            context.hold_days = 0
            print(f"{get_datetime()}: Closing position at {price:.2f} - Reason: {exit_reason}")

    # 记录回测指标
    record(price=price, in_pos=int(context.in_position))

# 保留 handle_data 函数但让它为空，避免与 schedule_function 冲突
def handle_data(context, data):
    pass