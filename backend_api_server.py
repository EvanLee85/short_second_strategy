#!/usr/bin/env python3
"""
后端API服务器
为前端仪表盘提供REST API和WebSocket服务

运行方式:
python backend_api_server.py

API端点:
- GET /api/v1/macro/overview - 宏观环境概览
- GET /api/v1/sector/rotation - 板块轮动分析
- GET /api/v1/stocks/candidates - 股票候选池
- GET /api/v1/trading/positions - 交易持仓
- WebSocket: /socket.io/ - 实时数据推送
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import pandas as pd
import numpy as np

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局状态存储
class GlobalState:
    def __init__(self):
        self.clients = {}  # 存储连接的客户端
        self.subscriptions = {}  # 存储订阅关系
        self.last_update = datetime.now()
        
        # 模拟数据存储
        self.macro_data = self._init_macro_data()
        self.sector_data = self._init_sector_data()
        self.stocks_data = self._init_stocks_data()
        self.trading_data = self._init_trading_data()
    
    def _init_macro_data(self):
        """初始化宏观数据"""
        return {
            "summary": [
                {"value": "5/6", "label": "宏观条件通过", "status": "positive"},
                {"value": "4/4", "label": "硬条件满足", "status": "positive"},
                {"value": "1/2", "label": "软条件警告", "status": "warning"},
                {"value": "85%", "label": "整体健康度", "status": "positive"}
            ],
            "indicators": {
                "index_trend": {
                    "value": 3856.42,
                    "ma50": 3820.15,
                    "status": "pass",
                    "health": 85
                },
                "market_breadth": {
                    "value": 52,
                    "threshold": 55,
                    "status": "warning",
                    "health": 52
                },
                "northbound_funds": {
                    "value": 42.6,
                    "threshold": 35.0,
                    "status": "pass",
                    "health": 78
                },
                "global_environment": {
                    "vix": 18.4,
                    "vix_threshold": 25.0,
                    "sp500": 0.3,
                    "nasdaq": 0.5,
                    "status": "pass",
                    "health": 92
                },
                "leverage_constraint": {
                    "margin_growth": 3.8,
                    "margin_threshold": 4.0,
                    "margin_ratio": 7.2,
                    "ratio_threshold": 8.0,
                    "status": "pass",
                    "health": 72
                },
                "a50_impact": {
                    "a50_change": 0.8,
                    "threshold": -1.0,
                    "status": "pass",
                    "health": 80
                }
            },
            "last_update": datetime.now().isoformat()
        }
    
    def _init_sector_data(self):
        """初始化板块数据"""
        return {
            "summary": [
                {"value": "5/6", "label": "轮动步骤通过", "status": "positive"},
                {"value": "85%", "label": "确认度", "status": "warning"},
                {"value": "AI", "label": "当前热点", "status": "positive"},
                {"value": "+22.3亿", "label": "资金净流入", "status": "positive"}
            ],
            "rotation_steps": {
                "strength_comparison": {"status": "pass", "score": 90},
                "sector_breadth": {"status": "pass", "score": 68},
                "time_continuation": {"status": "warning", "score": 50},
                "capital_ratio": {"status": "pass", "score": 85},
                "institution_support": {"status": "pass", "score": 88},
                "hidden_funds": {"status": "pass", "score": 92}
            },
            "sectors": [
                {
                    "name": "人工智能",
                    "rank": 2,
                    "rank_change": 7,
                    "volume": 268.5,
                    "rise_ratio": 68,
                    "main_inflow": 22.3,
                    "status": "强势轮入"
                },
                {
                    "name": "新能源汽车", 
                    "rank": 13,
                    "rank_change": -8,
                    "volume": 156.2,
                    "rise_ratio": 32,
                    "main_inflow": -15.6,
                    "status": "资金流出"
                },
                {
                    "name": "医药生物",
                    "rank": 8,
                    "rank_change": 0,
                    "volume": 89.6,
                    "rise_ratio": 38,
                    "main_inflow": -2.1,
                    "status": "横盘整理"
                }
            ],
            "last_update": datetime.now().isoformat()
        }
    
    def _init_stocks_data(self):
        """初始化股票数据"""
        return {
            "summary": [
                {"value": "1", "label": "一线龙头确认", "status": "positive"},
                {"value": "3", "label": "二线候选池", "status": "positive"},
                {"value": "2板", "label": "一线连板数", "status": "warning"},
                {"value": "良好", "label": "时序窗口", "status": "positive"}
            ],
            "first_tier": [
                {
                    "symbol": "002230",
                    "name": "科大讯飞",
                    "boards": 2,
                    "volume": 45.6,
                    "main_inflow": 8.9,
                    "dragon_tiger": "机构重仓",
                    "timing_risk": "窗口良好",
                    "suggestion": "观察为主"
                }
            ],
            "candidates": [
                {
                    "symbol": "002415",
                    "name": "海康威视",
                    "volume_rank": 4,
                    "market_cap": 356,
                    "relative_strength": 0.87,
                    "main_inflow": 2.3,
                    "pe_ratio": 18.5,
                    "timing": "T+0最佳",
                    "ev_net": 1.3,
                    "rating": "优秀",
                    "sector": "AI"
                },
                {
                    "symbol": "000858",
                    "name": "五粮液",
                    "volume_rank": 6,
                    "market_cap": 645,
                    "relative_strength": 0.92,
                    "main_inflow": 1.8,
                    "pe_ratio": 22.1,
                    "timing": "T+1较好",
                    "ev_net": 0.8,
                    "rating": "良好",
                    "sector": "消费"
                },
                {
                    "symbol": "300750",
                    "name": "宁德时代",
                    "volume_rank": 5,
                    "market_cap": 756,
                    "relative_strength": 0.83,
                    "main_inflow": 0.5,
                    "pe_ratio": 28.6,
                    "timing": "T+2观察",
                    "ev_net": 0.4,
                    "rating": "观察",
                    "sector": "新能源"
                }
            ],
            "last_update": datetime.now().isoformat()
        }
    
    def _init_trading_data(self):
        """初始化交易数据"""
        return {
            "summary": [
                {"value": "2", "label": "持仓数量", "status": "positive"},
                {"value": "28%", "label": "总仓位", "status": "warning"},
                {"value": "+1.8%", "label": "今日收益", "status": "positive"},
                {"value": "2.1", "label": "平均RR", "status": "positive"}
            ],
            "gates": {
                "risk_reward": {"value": 2.1, "threshold": 2.0, "status": "pass"},
                "win_rate": {"value": 0.63, "threshold": 0.60, "status": "pass"},
                "ev_net": {"value": 1.1, "threshold": 0.6, "status": "pass"}
            },
            "positions": [
                {
                    "symbol": "002415",
                    "position": 15,
                    "cost_price": 52.30,
                    "current_price": 54.20,
                    "pnl_percent": 3.6,
                    "stop_loss": 50.10,
                    "target": 55.40,
                    "remaining_days": 3
                },
                {
                    "symbol": "000858", 
                    "position": 13,
                    "cost_price": 186.50,
                    "current_price": 185.20,
                    "pnl_percent": -0.7,
                    "stop_loss": 182.30,
                    "target": 195.60,
                    "remaining_days": 2
                }
            ],
            "last_update": datetime.now().isoformat()
        }

state = GlobalState()

# ===== REST API 端点 =====

@app.route('/api/v1/macro/overview', methods=['GET'])
def get_macro_overview():
    """获取宏观环境概览"""
    try:
        # 模拟数据更新
        state.macro_data['last_update'] = datetime.now().isoformat()
        
        # 添加一些随机波动
        import random
        state.macro_data['indicators']['index_trend']['value'] += random.uniform(-5, 5)
        state.macro_data['indicators']['market_breadth']['value'] += random.randint(-2, 3)
        
        return jsonify({
            "status": "success",
            "data": state.macro_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取宏观数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/macro/history', methods=['GET'])
def get_macro_history():
    """获取宏观环境历史数据"""
    days = request.args.get('days', 30, type=int)
    
    try:
        # 生成模拟历史数据
        history_data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            history_data.append({
                "date": date.isoformat(),
                "index_value": 3800 + np.random.normal(0, 50),
                "market_breadth": 50 + np.random.normal(0, 10),
                "northbound": np.random.normal(40, 20),
                "health_score": np.random.uniform(70, 90)
            })
        
        return jsonify({
            "status": "success", 
            "data": history_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取宏观历史数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/sector/rotation', methods=['GET'])
def get_sector_rotation():
    """获取板块轮动分析"""
    try:
        state.sector_data['last_update'] = datetime.now().isoformat()
        
        return jsonify({
            "status": "success",
            "data": state.sector_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取板块轮动数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/sector/<sector_code>/analysis', methods=['GET'])
def get_sector_analysis(sector_code):
    """获取特定板块分析"""
    try:
        # 模拟板块详细分析数据
        analysis = {
            "sector_code": sector_code,
            "detailed_metrics": {
                "momentum": np.random.uniform(0.6, 1.0),
                "breadth": np.random.uniform(50, 80),
                "volume_surge": np.random.uniform(1.2, 2.5),
                "institutions": np.random.choice(['买入', '观察', '卖出'])
            },
            "key_stocks": [
                {"symbol": f"00{np.random.randint(1000, 9999)}", "contribution": np.random.uniform(10, 30)}
                for _ in range(5)
            ]
        }
        
        return jsonify({
            "status": "success",
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取板块分析失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/stocks/candidates', methods=['GET'])
def get_stock_candidates():
    """获取股票候选池"""
    try:
        # 获取筛选参数
        sector_filter = request.args.get('sector', '')
        market_cap = request.args.get('marketCap', '')
        technical = request.args.get('technical', '')
        
        candidates = state.stocks_data['candidates'].copy()
        
        # 应用筛选条件
        if sector_filter:
            candidates = [s for s in candidates if s.get('sector', '').upper() == sector_filter.upper()]
        
        if market_cap:
            if market_cap == 'large':
                candidates = [s for s in candidates if s['market_cap'] > 500]
            elif market_cap == 'mid':
                candidates = [s for s in candidates if 100 <= s['market_cap'] <= 500]
            elif market_cap == 'small':
                candidates = [s for s in candidates if s['market_cap'] < 100]
        
        filtered_data = state.stocks_data.copy()
        filtered_data['candidates'] = candidates
        filtered_data['last_update'] = datetime.now().isoformat()
        
        return jsonify({
            "status": "success",
            "data": filtered_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取股票候选池失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/stocks/<symbol>/detail', methods=['GET'])
def get_stock_detail(symbol):
    """获取股票详细信息"""
    try:
        # 查找股票
        stock = None
        for candidate in state.stocks_data['candidates']:
            if candidate['symbol'] == symbol:
                stock = candidate
                break
        
        if not stock:
            return jsonify({"status": "error", "message": "股票未找到"}), 404
        
        # 生成详细数据
        detail = stock.copy()
        detail.update({
            "technical_indicators": {
                "ma5": np.random.uniform(50, 60),
                "ma20": np.random.uniform(45, 55), 
                "rsi": np.random.uniform(30, 70),
                "macd": np.random.uniform(-1, 1)
            },
            "fundamentals": {
                "roe": np.random.uniform(8, 20),
                "debt_ratio": np.random.uniform(20, 60),
                "growth_rate": np.random.uniform(-10, 30)
            }
        })
        
        return jsonify({
            "status": "success",
            "data": detail,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/stocks/<symbol>/buypoint', methods=['GET'])
def get_buypoint_analysis(symbol):
    """获取买点分析"""
    try:
        analysis = {
            "symbol": symbol,
            "pattern": np.random.choice(["突破形态", "回调形态", "整理形态"]),
            "buyPointType": np.random.choice(["T+0最佳", "T+1较好", "T+2观察"]),
            "winRate": f"{np.random.randint(55, 75)}%",
            "riskReward": round(np.random.uniform(1.8, 3.2), 2),
            "timeNodes": [
                {"time": "09:30-10:00", "event": "开盘拉升确认", "status": "pass"},
                {"time": "10:15-10:30", "event": "回调不破支撑", "status": "pass"},
                {"time": "13:00-13:15", "event": "二次拉升买点", "status": "recommend"}
            ],
            "suggestion": "午盘二次拉升时介入，止损设在今日最低点下方2%，目标位看前高阻力。"
        }
        
        return jsonify({
            "status": "success", 
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取买点分析失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/trading/positions', methods=['GET'])
def get_trading_positions():
    """获取交易持仓"""
    try:
        # 更新当前价格（模拟实时变动）
        for position in state.trading_data['positions']:
            price_change = np.random.uniform(-0.02, 0.02)  # ±2%随机变动
            position['current_price'] *= (1 + price_change)
            position['pnl_percent'] = ((position['current_price'] - position['cost_price']) / position['cost_price']) * 100
        
        state.trading_data['last_update'] = datetime.now().isoformat()
        
        return jsonify({
            "status": "success",
            "data": state.trading_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取交易持仓失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/trading/history', methods=['GET'])
def get_trade_history():
    """获取交易历史"""
    days = request.args.get('days', 7, type=int)
    
    try:
        # 生成模拟交易历史
        history = []
        for i in range(np.random.randint(5, 15)):  # 随机5-15笔交易
            history.append({
                "id": str(uuid.uuid4()),
                "symbol": np.random.choice(['002415', '000858', '300750', '002230']),
                "action": np.random.choice(['买入', '卖出']),
                "price": round(np.random.uniform(20, 200), 2),
                "quantity": np.random.randint(100, 1000),
                "timestamp": (datetime.now() - timedelta(days=np.random.randint(0, days))).isoformat(),
                "pnl": round(np.random.uniform(-5, 10), 2)
            })
        
        return jsonify({
            "status": "success",
            "data": {"trades": history},
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取交易历史失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/risk/metrics', methods=['GET'])
def get_risk_metrics():
    """获取风险指标"""
    try:
        metrics = {
            "portfolio_var": np.random.uniform(1, 5),
            "max_drawdown": np.random.uniform(5, 15),
            "sharpe_ratio": np.random.uniform(0.8, 2.5),
            "position_concentration": np.random.uniform(15, 35),
            "sector_exposure": {
                "AI": np.random.uniform(20, 40),
                "消费": np.random.uniform(10, 30),
                "新能源": np.random.uniform(5, 25)
            }
        }
        
        return jsonify({
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ===== WebSocket 事件处理 =====

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    client_id = str(uuid.uuid4())
    state.clients[request.sid] = {
        'id': client_id,
        'connected_at': datetime.now(),
        'subscriptions': set()
    }
    
    logger.info(f"客户端连接: {request.sid}")
    emit('connected', {'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    if request.sid in state.clients:
        del state.clients[request.sid]
    
    if request.sid in state.subscriptions:
        del state.subscriptions[request.sid]
    
    logger.info(f"客户端断开: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """处理数据流订阅"""
    stream = data.get('stream')
    if not stream:
        emit('error', {'message': '缺少stream参数'})
        return
    
    # 记录订阅
    if request.sid not in state.subscriptions:
        state.subscriptions[request.sid] = set()
    
    state.subscriptions[request.sid].add(stream)
    
    if request.sid in state.clients:
        state.clients[request.sid]['subscriptions'].add(stream)
    
    # 加入对应的房间
    join_room(f'stream_{stream}')
    
    logger.info(f"客户端 {request.sid} 订阅: {stream}")
    emit('subscribed', {'stream': stream})
    
    # 立即发送一次当前数据
    send_stream_data(stream)

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """取消订阅"""
    stream = data.get('stream')
    if not stream:
        return
    
    if request.sid in state.subscriptions:
        state.subscriptions[request.sid].discard(stream)
    
    if request.sid in state.clients:
        state.clients[request.sid]['subscriptions'].discard(stream)
    
    leave_room(f'stream_{stream}')
    
    logger.info(f"客户端 {request.sid} 取消订阅: {stream}")
    emit('unsubscribed', {'stream': stream})

@socketio.on('ping')
def handle_ping():
    """心跳检测"""
    emit('pong')

def send_stream_data(stream):
    """发送流数据"""
    try:
        if stream == 'macro_data':
            socketio.emit('macro_update', {
                'data': state.macro_data,
                'message': '宏观环境数据更新',
                'timestamp': datetime.now().isoformat()
            }, room=f'stream_{stream}')
            
        elif stream == 'sector_rotation':
            socketio.emit('sector_update', {
                'data': state.sector_data, 
                'sector': '人工智能',
                'status': '强势轮入',
                'timestamp': datetime.now().isoformat()
            }, room=f'stream_{stream}')
            
        elif stream == 'stock_candidates':
            socketio.emit('stocks_update', {
                'data': state.stocks_data,
                'added': np.random.randint(0, 3),
                'removed': np.random.randint(0, 2),
                'timestamp': datetime.now().isoformat()
            }, room=f'stream_{stream}')
            
        elif stream == 'trading_execution':
            socketio.emit('trading_update', {
                'data': state.trading_data,
                'symbol': np.random.choice(['002415', '000858']),
                'action': np.random.choice(['价格更新', '仓位调整']),
                'price': round(np.random.uniform(50, 200), 2),
                'timestamp': datetime.now().isoformat()
            }, room=f'stream_{stream}')
            
        elif stream == 'realtime_quotes':
            # 发送实时行情tick数据
            symbol = np.random.choice(['002415', '000858', '300750', '002230'])
            price = round(np.random.uniform(50, 200), 2)
            change = round(np.random.uniform(-3, 3), 2)
            
            socketio.emit('tick_data', {
                'symbol': symbol,
                'price': price,
                'change': change,
                'timestamp': datetime.now().isoformat()
            }, room=f'stream_{stream}')
            
    except Exception as e:
        logger.error(f"发送流数据失败 ({stream}): {e}")

# 定时任务：模拟实时数据推送
def background_data_push():
    """后台数据推送任务"""
    while True:
        try:
            # 每隔几秒推送不同类型的数据
            import time
            time.sleep(5)
            
            # 随机选择要推送的数据流
            active_streams = set()
            for subscriptions in state.subscriptions.values():
                active_streams.update(subscriptions)
            
            if active_streams:
                stream = np.random.choice(list(active_streams))
                send_stream_data(stream)
                
        except Exception as e:
            logger.error(f"后台推送任务错误: {e}")
            time.sleep(10)

# 静态文件服务
@app.route('/')
def serve_dashboard():
    """服务前端仪表盘"""
    return send_from_directory('frontend', 'frontend_dashboard_system.html')

@app.route('/frontend/<path:filename>')
def serve_frontend_files(filename):
    """服务前端静态文件"""
    return send_from_directory('frontend', filename)

# 健康检查
@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "clients_connected": len(state.clients),
        "active_subscriptions": len(state.subscriptions)
    })

if __name__ == '__main__':
    # 启动后台推送任务
    import threading
    background_thread = threading.Thread(target=background_data_push, daemon=True)
    background_thread.start()
    
    logger.info("启动量化交易API服务器...")
    logger.info("前端仪表盘: http://localhost:5000/")
    logger.info("API文档: http://localhost:5000/api/v1/")
    
    # 启动服务器
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)