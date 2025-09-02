// frontend/js/api/endpoints.js
// 统一端点封装：定义所有与后端通信的接口函数。
// 每个函数返回 { ok, data, error, status }，由 http.js 保证统一格式。
// 此处仅关注业务路径与入参/出参的定义。

import { get, post } from './http.js';

// 健康检查：GET /api/v1/health
export function getHealth() {
  return get('/api/v1/health');
}

// 宏观状态：GET /api/v1/macro/status
export function getMacroStatus() {
  return get('/api/v1/macro/status');
}

// 板块轮动：GET /api/v1/sectors/rotation?sector=AI
export function getSectorsRotation(sector) {
  const params = sector ? { sector } : null;
  return get('/api/v1/sectors/rotation', params);
}

// 龙头筛选：GET /api/v1/stocks/leaders?type=first-line|second-line&sector=AI
export function getStocksLeaders({ type, sector } = {}) {
  const params = {};
  if (type) params.type = type;
  if (sector) params.sector = sector;
  return get('/api/v1/stocks/leaders', params);
}

// 入场信号评估：POST /api/v1/trades/signal
export function postTradeSignal(payload) {
  return post('/api/v1/trades/signal', payload);
}

// 风险：交易闸门评估
export function postRiskEvaluate(payload) {
  return post('/api/v1/risk/evaluate', payload);
}

// 风险：仓位建议
export function postRiskPosition(payload) {
  return post('/api/v1/risk/position', payload);
}

// 风险：撤退计划
export function postRiskExitPlan(payload) {
  return post('/api/v1/risk/exit-plan', payload);
}

// 纸上交易：开仓
export function postPaperOpen(payload) {
  return post('/api/v1/paper/open', payload);
}

// 纸上交易：推进行情
export function postPaperStep(payload) {
  return post('/api/v1/paper/step', payload);
}

// 纸上交易：查询状态
export function getPaperState() {
  return get('/api/v1/paper/state');
}

// 默认导出一个聚合对象，方便一次性引入
const api = {
  getHealth,
  getMacroStatus,
  getSectorsRotation,
  getStocksLeaders,
  postTradeSignal,
  postRiskEvaluate,
  postRiskPosition,
  postRiskExitPlan,
  postPaperOpen,
  postPaperStep,
  getPaperState,
};
export default api;

// 在浏览器环境挂到 window，便于控制台调试
if (typeof window !== 'undefined') {
  window.api = api;
}