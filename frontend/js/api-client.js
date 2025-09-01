// frontend/js/api-client.js
/**
 * API客户端模块
 * 处理所有与后端API的HTTP请求通信
 */

class APIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    // 基础请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error(`API请求失败 ${endpoint}:`, error);
            throw error;
        }
    }

    // GET请求
    async get(endpoint, params = {}) {
        const urlParams = new URLSearchParams(params);
        const queryString = urlParams.toString();
        const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(fullEndpoint, { method: 'GET' });
    }

    // POST请求
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT请求
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // === 宏观环境API ===
    async getMacroOverview() {
        return this.get('/macro/overview');
    }

    async getMacroHistory(days = 30) {
        return this.get('/macro/history', { days });
    }

    async updateMacroThresholds(thresholds) {
        return this.post('/macro/thresholds', thresholds);
    }

    // === 板块轮动API ===
    async getSectorRotation() {
        return this.get('/sector/rotation');
    }

    async getSectorAnalysis(sectorCode) {
        return this.get(`/sector/${sectorCode}/analysis`);
    }

    async getSectorHistory(sectorCode, days = 7) {
        return this.get(`/sector/${sectorCode}/history`, { days });
    }

    // === 股票筛选API ===
    async getStockCandidates(filters = {}) {
        return this.get('/stocks/candidates', filters);
    }

    async getStockDetail(symbol) {
        return this.get(`/stocks/${symbol}/detail`);
    }

    async getBuyPointAnalysis(symbol) {
        return this.get(`/stocks/${symbol}/buypoint`);
    }

    async getStockChart(symbol, period = '1d') {
        return this.get(`/stocks/${symbol}/chart`, { period });
    }

    // === 交易执行API ===
    async getTradingPositions() {
        return this.get('/trading/positions');
    }

    async getTradeHistory(days = 7) {
        return this.get('/trading/history', { days });
    }

    async submitOrder(orderData) {
        return this.post('/trading/orders', orderData);
    }

    async updatePosition(symbol, action, amount) {
        return this.put(`/trading/positions/${symbol}`, { action, amount });
    }

    // === 风险管理API ===
    async getRiskMetrics() {
        return this.get('/risk/metrics');
    }

    async getPortfolioRisk() {
        return this.get('/risk/portfolio');
    }

    // === 回测分析API ===
    async getBacktestResults(strategyId) {
        return this.get(`/backtest/${strategyId}/results`);
    }

    async runBacktest(config) {
        return this.post('/backtest/run', config);
    }
}

// 导出API客户端实例
window.apiClient = new APIClient();