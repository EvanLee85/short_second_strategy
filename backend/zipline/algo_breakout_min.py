# -*- coding: utf-8 -*-
"""
最小可用：20日高点突破 + 简单RR风控 + 时间止盈/止损
- 数据频率：日线（已用 csvdir_equities -> sss_csv 导入）
- 资产：symbol('TEST')（与 sss_csv 中 CSV 一致）
- 逻辑：
  1) 若今日收盘 >= 过去20日最高价*(1+margin) 且 当前无仓 -> 满仓至 95%
  2) 持仓后：
     - 达到目标价(入场 + 2*ATR) 或 跌破止损(入场 - 1*ATR) -> 清仓
     - 或持仓超过 max_holding_days -> 清仓
"""

from zipline.api import (
    order_target_percent, record, symbol,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, commission, slippage,
    get_datetime
)
import numpy as np
import pandas as pd

def initialize(context):
    # === 交易参数（可视需要调优） ===
    context.asset = symbol('TEST')         # 与 sss_csv 中的 CSV 名一致
    context.margin = 0.0                   # 突破加点 - 降低为0，更容易触发
    context.lookback = 10                  # 突破回看窗口 - 缩短到10天
    context.atr_n = 14
    context.atr_k_up = 2.0
    context.atr_k_dn = 1.0
    context.max_holding_days = 10

    context.entry_price = None
    context.holding_days = 0
    context.warmup_days = 0  # 用于追踪预热期

    # === 交易成本与滑点（A股常见设置可再校准） ===
    set_commission(commission.PerShare(cost=0.0005, min_trade_cost=0.0))  # 手续费 ~万5（示例）
    set_slippage(slippage.FixedSlippage(spread=0.0))

    # 每日开盘30分钟后检查/调整仓位
    schedule_function(
        rebalance,
        date_rules.every_day(),
        time_rules.market_open(minutes=30)
    )

def _compute_atr(data, asset, n=14):
    """
    使用 history 计算简化 ATR（不依赖外部指标模块，保证 Zipline 内部可独立运行）
    处理历史数据不足的情况
    """
    try:
        # 先检查能获取多少历史数据
        needed = n + 1
        
        # 尝试获取数据，如果失败则减少需求量
        try:
            h = data.history(asset, 'high', needed, '1d').values
            l = data.history(asset, 'low',  needed, '1d').values
            c = data.history(asset, 'close', needed, '1d').values
        except:
            # 如果历史数据不足，尝试获取更少的数据
            available = min(5, needed)  # 至少需要5天数据计算ATR
            try:
                h = data.history(asset, 'high', available, '1d').values
                l = data.history(asset, 'low',  available, '1d').values
                c = data.history(asset, 'close', available, '1d').values
            except:
                # 如果连5天数据都没有，返回0
                return 0.0

        if len(c) < 2:
            return 0.0

        # True Range: max(high-low, abs(high-prev_close), abs(low-prev_close))
        prev_c = c[:-1]
        tr1 = h[1:] - l[1:]
        tr2 = np.abs(h[1:] - prev_c)
        tr3 = np.abs(l[1:] - prev_c)
        tr = np.maximum.reduce([tr1, tr2, tr3])

        # 简化：最近n根 TR 的均值作为 ATR
        if len(tr) > 0:
            atr = float(np.mean(tr[-min(n, len(tr)):]))
        else:
            atr = 0.0
            
        return atr
    except Exception as e:
        # 任何错误都返回0
        return 0.0

def rebalance(context, data):
    asset = context.asset
    if not data.can_trade(asset):
        return

    # 记录预热期天数
    context.warmup_days += 1
    
    # 获取当前日期，用于调试
    current_date = get_datetime()
    
    # 当前价格
    close = float(data.current(asset, 'close'))
    
    # 安全地获取历史高点
    try:
        # 判断有多少历史数据可用
        lookback_actual = min(context.lookback + 1, context.warmup_days)
        
        if lookback_actual < 2:
            # 数据太少，不交易
            record(price=close, has_pos=0.0, atr=0.0)
            return
            
        highs = data.history(asset, 'high', lookback_actual, '1d')
        # 仅用"过去 lookback 天"的最高价，不含当日
        if len(highs) > 1:
            high_n = float(highs.iloc[:-1].max())
        else:
            high_n = float(highs.max())
    except Exception as e:
        # 如果获取历史数据失败，记录并跳过
        record(price=close, has_pos=0.0, atr=0.0)
        return

    threshold = high_n * (1.0 + context.margin)

    pos_amount = context.portfolio.positions[asset].amount
    has_pos = pos_amount != 0

    # 计算 ATR 作为目标/止损的尺度
    atr = _compute_atr(data, asset, n=context.atr_n)
    target = None
    stop = None

    # === 开仓条件：突破 10日高点 ===
    # 降低预热期要求，从20天改为10天
    if (not has_pos) and (close >= threshold) and (context.warmup_days >= context.lookback):
        order_target_percent(asset, 0.95)
        context.entry_price = close
        context.holding_days = 0

    # === 持仓风控：2*ATR 止盈 / 1*ATR 止损 / 持仓天数止盈止损 ===
    elif has_pos:
        if context.entry_price is None:
            context.entry_price = close

        target = context.entry_price + context.atr_k_up * atr
        stop   = context.entry_price - context.atr_k_dn * atr

        exit_now = False
        if atr > 0:
            if close >= target:
                exit_now = True
            elif close <= stop:
                exit_now = True

        # 时间止损/止盈（避免长时间套牢）
        context.holding_days += 1
        if context.holding_days >= context.max_holding_days:
            exit_now = True

        if exit_now:
            order_target_percent(asset, 0.0)
            context.entry_price = None
            context.holding_days = 0

    # 记录便于回看
    record(price=close, has_pos=float(has_pos), atr=atr or 0.0)