// frontend/js/dashboard-core.js
/**
 * 仪表盘核心模块
 * 统一管理UI状态、数据流和用户交互
 */

class DashboardCore {
    constructor() {
        this.currentTab = 'macro';
        this.filters = {
            sector: '',
            marketCap: '',
            technical: ''
        };
        this.updateTimers = new Map();
        this.chartInstances = new Map();
        this.modalStack = [];
    }

    // 初始化仪表盘
    async init() {
        console.log('初始化仪表盘核心...');
        
        // 初始化API客户端
        if (!window.apiClient) {
            window.apiClient = new APIClient();
        }

        // 初始化WebSocket客户端
        if (!window.wsClient) {
            window.wsClient = new WebSocketClient();
        }

        // 建立WebSocket连接
        window.wsClient.connect();
        
        // 订阅实时数据流
        this.subscribeToDataStreams();
        
        // 恢复上次访问的页面
        this.restoreLastTab();
        
        // 加载初始数据
        await this.loadInitialData();
        
        // 设置定时更新
        this.setupPeriodicUpdates();
        
        // 绑定事件监听器
        this.bindEventListeners();
        
        console.log('仪表盘初始化完成');
    }

    // 订阅实时数据流
    subscribeToDataStreams() {
        if (window.wsClient.isConnected()) {
            window.wsClient.subscribe('macro_data');
            window.wsClient.subscribe('sector_rotation');
            window.wsClient.subscribe('stock_candidates');
            window.wsClient.subscribe('trading_execution');
            window.wsClient.subscribe('realtime_quotes');
        }
        
        // 监听连接状态变化
        window.wsClient.on('connectionStatusChanged', ({ status }) => {
            if (status === 'connected') {
                this.subscribeToDataStreams();
            }
        });
    }

    // 恢复上次标签页
    restoreLastTab() {
        const lastTab = localStorage.getItem('currentTab') || 'macro';
        this.switchTab(lastTab);
    }

    // 加载初始数据
    async loadInitialData() {
        try {
            // 根据当前标签页加载对应数据
            await this.loadTabData(this.currentTab);
            
            this.addLog('仪表盘数据加载完成', 'success');
        } catch (error) {
            this.addLog(`初始数据加载失败: ${error.message}`, 'error');
        }
    }

    // 设置定时更新
    setupPeriodicUpdates() {
        // 每分钟更新一次宏观数据
        this.updateTimers.set('macro', setInterval(() => {
            if (this.currentTab === 'macro') {
                this.loadTabData('macro');
            }
        }, 60000));

        // 每30秒更新一次股票数据
        this.updateTimers.set('stocks', setInterval(() => {
            if (this.currentTab === 'stocks') {
                this.loadTabData('stocks');
            }
        }, 30000));

        // 每15秒更新一次交易数据
        this.updateTimers.set('trading', setInterval(() => {
            if (this.currentTab === 'trading') {
                this.loadTabData('trading');
            }
        }, 15000));
    }

    // 绑定事件监听器
    bindEventListeners() {
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchTab('macro');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchTab('sector');
                        break;
                    case '3':
                        e.preventDefault();
                        this.switchTab('stocks');
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshCurrentTab();
                        break;
                }
            }
        });

        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // 页面隐藏时降低更新频率
                this.pauseUpdates();
            } else {
                // 页面显示时恢复更新
                this.resumeUpdates();
            }
        });

        // 窗口关闭前清理
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    // 标签页切换
    switchTab(tabName) {
        // 隐藏所有标签页内容
        const contents = document.querySelectorAll('.tab-content');
        contents.forEach(content => content.classList.remove('active'));
        
        // 移除所有标签的激活状态
        const tabs = document.querySelectorAll('.nav-tab');
        tabs.forEach(tab => tab.classList.remove('active'));
        
        // 显示选中的标签页内容
        const targetContent = document.getElementById(`${tabName}-tab`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
        
        // 激活选中的标签
        const targetTab = document.querySelector(`[onclick*="${tabName}"]`);
        if (targetTab) {
            targetTab.classList.add('active');
        }
        
        // 更新状态
        this.currentTab = tabName;
        localStorage.setItem('currentTab', tabName);
        
        // 加载标签页数据
        this.loadTabData(tabName);
        
        this.addLog(`切换到${this.getTabName(tabName)}页面`, 'info');
    }

    // 获取标签页中文名
    getTabName(tabName) {
        const nameMap = {
            'macro': '宏观环境',
            'sector': '板块轮动',
            'stocks': '股票筛选',
            'trading': '交易执行',
            'risk': '风险管理',
            'backtest': '回测分析'
        };
        return nameMap[tabName] || tabName;
    }

    // 加载标签页数据
    async loadTabData(tabName) {
        try {
            switch(tabName) {
                case 'macro':
                    const macroData = await window.apiClient.getMacroOverview();
                    this.updateMacroDisplay(macroData);
                    break;
                    
                case 'sector':
                    const sectorData = await window.apiClient.getSectorRotation();
                    this.updateSectorDisplay(sectorData);
                    break;
                    
                case 'stocks':
                    const stocksData = await window.apiClient.getStockCandidates(this.filters);
                    this.updateStocksDisplay(stocksData);
                    break;
                    
                case 'trading':
                    const tradingData = await window.apiClient.getTradingPositions();
                    this.updateTradingDisplay(tradingData);
                    break;
                    
                case 'risk':
                    const riskData = await window.apiClient.getRiskMetrics();
                    this.updateRiskDisplay(riskData);
                    break;
                    
                case 'backtest':
                    const backtestData = await window.apiClient.getBacktestResults('default');
                    this.updateBacktestDisplay(backtestData);
                    break;
            }
        } catch (error) {
            this.addLog(`${this.getTabName(tabName)}数据加载失败: ${error.message}`, 'error');
        }
    }

    // 更新宏观显示
    updateMacroDisplay(data) {
        if (!data) return;
        
        // 更新状态汇总
        this.updateStatusSummary('macro', data.summary);
        
        // 更新宏观指标
        if (data.indicators) {
            this.updateMacroIndicators(data.indicators);
        }
        
        this.addLog('宏观环境数据更新完成', 'info');
    }

    // 更新板块显示
    updateSectorDisplay(data) {
        if (!data) return;
        
        this.updateStatusSummary('sector', data.summary);
        
        if (data.sectors) {
            this.updateSectorTable(data.sectors);
        }
        
        this.addLog('板块轮动数据更新完成', 'info');
    }

    // 更新股票显示
    updateStocksDisplay(data) {
        if (!data) return;
        
        this.updateStatusSummary('stocks', data.summary);
        
        if (data.candidates) {
            this.updateStocksTable(data.candidates);
        }
        
        this.addLog(`股票筛选更新: ${data.candidates?.length || 0}只股票`, 'info');
    }

    // 更新交易显示
    updateTradingDisplay(data) {
        if (!data) return;
        
        this.updateStatusSummary('trading', data.summary);
        
        if (data.positions) {
            this.updatePositionsTable(data.positions);
        }
        
        this.addLog('交易执行数据更新完成', 'info');
    }

    // 更新风险显示
    updateRiskDisplay(data) {
        if (!data) return;
        
        // 实现风险管理显示逻辑
        this.addLog('风险管理数据更新完成', 'info');
    }

    // 更新回测显示
    updateBacktestDisplay(data) {
        if (!data) return;
        
        // 实现回测分析显示逻辑
        this.addLog('回测分析数据更新完成', 'info');
    }

    // 更新实时价格
    updateRealtimePrice(symbol, price, change) {
        const rows = document.querySelectorAll(`tr[data-symbol="${symbol}"]`);
        rows.forEach(row => {
            const priceCell = row.querySelector('.realtime-price');
            if (priceCell) {
                priceCell.textContent = price.toFixed(2);
                priceCell.className = `realtime-price ${change >= 0 ? 'positive' : 'negative'}`;
            }
            
            const changeCell = row.querySelector('.realtime-change');
            if (changeCell) {
                const changePercent = ((change / (price - change)) * 100).toFixed(2);
                changeCell.textContent = `${change >= 0 ? '+' : ''}${changePercent}%`;
                changeCell.className = `realtime-change ${change >= 0 ? 'positive' : 'negative'}`;
            }
        });
    }

    // 辅助方法：更新状态汇总
    updateStatusSummary(tab, summaryData) {
        const summaryContainer = document.querySelector(`#${tab}-tab .status-summary`);
        if (!summaryContainer || !summaryData) return;
        
        const items = summaryContainer.querySelectorAll('.summary-item');
        items.forEach((item, index) => {
            if (summaryData[index]) {
                const valueEl = item.querySelector('.summary-value');
                const labelEl = item.querySelector('.summary-label');
                
                if (valueEl) valueEl.textContent = summaryData[index].value;
                if (labelEl) labelEl.textContent = summaryData[index].label;
                
                // 更新样式类
                item.className = `summary-item ${summaryData[index].status || ''}`;
            }
        });
    }

    // 日志系统
    addLog(message, type = 'info') {
        const logContainer = document.getElementById('macro-log');
        if (!logContainer) return;
        
        const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // 限制日志条数
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    // 刷新当前标签页
    async refreshCurrentTab() {
        await this.loadTabData(this.currentTab);
        this.addLog(`${this.getTabName(this.currentTab)}数据刷新完成`, 'success');
    }

    // 暂停更新
    pauseUpdates() {
        this.updateTimers.forEach(timer => clearInterval(timer));
    }

    // 恢复更新
    resumeUpdates() {
        this.setupPeriodicUpdates();
    }

    // 清理资源
    cleanup() {
        this.updateTimers.forEach(timer => clearInterval(timer));
        this.chartInstances.forEach(chart => chart.destroy());
        
        if (window.wsClient) {
            window.wsClient.disconnect();
        }
    }
}

// 导出仪表盘核心实例
window.dashboardCore = new DashboardCore();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardCore.init().catch(error => {
        console.error('仪表盘初始化失败:', error);
    });
});