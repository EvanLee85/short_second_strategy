// frontend/js/websocket-client.js
/**
 * WebSocket客户端模块
 * 处理实时数据订阅和推送 (第3层功能)
 */

class WebSocketClient {
    constructor(url = window.location.origin) {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.subscriptions = new Set();
        this.eventHandlers = new Map();
        this.connectionStatus = 'disconnected';
        this.heartbeatInterval = null;
    }

    // 连接WebSocket
    connect() {
        try {
            // 使用Socket.IO客户端
            this.socket = io(this.url, {
                transports: ['websocket', 'polling'],
                timeout: 20000,
                forceNew: true
            });

            this.setupEventHandlers();
            this.updateConnectionStatus('connecting');
            
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            this.updateConnectionStatus('disconnected');
            this.scheduleReconnect();
        }
    }

    // 设置事件处理器
    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('WebSocket连接成功');
            this.updateConnectionStatus('connected');
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            this.resubscribeAll();
        });

        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket连接断开:', reason);
            this.updateConnectionStatus('disconnected');
            this.stopHeartbeat();
            
            if (reason === 'io server disconnect') {
                // 服务器主动断开，需要重连
                this.scheduleReconnect();
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket连接错误:', error);
            this.updateConnectionStatus('error');
            this.scheduleReconnect();
        });

        // 业务数据事件处理
        this.socket.on('macro_update', (data) => this.handleMacroUpdate(data));
        this.socket.on('sector_update', (data) => this.handleSectorUpdate(data));
        this.socket.on('stock_update', (data) => this.handleStockUpdate(data));
        this.socket.on('trading_update', (data) => this.handleTradingUpdate(data));
        this.socket.on('tick_data', (data) => this.handleTickData(data));
        this.socket.on('news_update', (data) => this.handleNewsUpdate(data));
    }

    // 更新连接状态
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            const statusText = statusElement.querySelector('.status-text');
            
            statusElement.className = `connection-status ${status}`;
            
            switch(status) {
                case 'connected':
                    statusText.textContent = '实时连接';
                    break;
                case 'connecting':
                    statusText.textContent = '连接中...';
                    break;
                case 'disconnected':
                    statusText.textContent = '连接断开';
                    break;
                case 'error':
                    statusText.textContent = '连接错误';
                    break;
            }
        }

        // 触发自定义事件
        this.emit('connectionStatusChanged', { status });
    }

    // 开始心跳检测
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('ping');
            }
        }, 30000); // 30秒心跳
    }

    // 停止心跳检测
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    // 重连调度
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指数退避
            
            setTimeout(() => {
                console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, delay);
        } else {
            console.error('达到最大重连次数，停止重连');
            this.updateConnectionStatus('failed');
        }
    }

    // 订阅数据流
    subscribe(stream, params = {}) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('subscribe', { stream, params });
            this.subscriptions.add(stream);
            console.log(`已订阅数据流: ${stream}`);
        } else {
            console.warn('WebSocket未连接，订阅失败');
        }
    }

    // 取消订阅
    unsubscribe(stream) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('unsubscribe', { stream });
            this.subscriptions.delete(stream);
            console.log(`已取消订阅: ${stream}`);
        }
    }

    // 重新订阅所有流
    resubscribeAll() {
        this.subscriptions.forEach(stream => {
            this.subscribe(stream);
        });
    }

    // 数据处理方法
    handleMacroUpdate(data) {
        console.log('宏观数据更新:', data);
        this.emit('macroUpdate', data);
        
        // 更新UI
        if (window.dashboardCore) {
            window.dashboardCore.updateMacroDisplay(data);
        }
    }

    handleSectorUpdate(data) {
        console.log('板块数据更新:', data);
        this.emit('sectorUpdate', data);
        
        if (window.dashboardCore) {
            window.dashboardCore.updateSectorDisplay(data);
        }
    }

    handleStockUpdate(data) {
        console.log('股票数据更新:', data);
        this.emit('stockUpdate', data);
        
        if (window.dashboardCore) {
            window.dashboardCore.updateStocksDisplay(data);
        }
    }

    handleTradingUpdate(data) {
        console.log('交易数据更新:', data);
        this.emit('tradingUpdate', data);
        
        if (window.dashboardCore) {
            window.dashboardCore.updateTradingDisplay(data);
        }
    }

    handleTickData(data) {
        // 处理实时行情数据
        this.emit('tickData', data);
        
        if (window.dashboardCore) {
            window.dashboardCore.updateRealtimePrice(data.symbol, data.price, data.change);
        }
    }

    handleNewsUpdate(data) {
        console.log('新闻更新:', data);
        this.emit('newsUpdate', data);
    }

    // 事件系统
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }

    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).delete(handler);
        }
    }

    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    // 断开连接
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.stopHeartbeat();
        this.updateConnectionStatus('disconnected');
    }

    // 获取连接状态
    isConnected() {
        return this.socket && this.socket.connected;
    }
}

// 导出WebSocket客户端实例
window.wsClient = new WebSocketClient();