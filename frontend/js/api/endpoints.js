// frontend/js/api/endpoints.js
// 统一端点封装（全部中文注释）：
// - 所有函数都返回 { ok, data, error, status } 结构（由 http.js 保证）。
// - 这里仅关心业务路径与入参/出参的说明。
// - 兼容两种导出方式：命名导出 & 默认导出（default 为一个包含所有函数的对象）。

import { get, post } from './http.js';

/** 健康检查：GET /api/v1/health */
export function getHealth() {
  return get('/api/v1/health');
}

/** 宏观状态（风控/哨兵）：GET /api/v1/macro/status */
export function getMacroStatus() {
  return get('/api/v1/macro/status');
}

/** 板块轮动：GET /api/v1/sectors/rotation?sector=AI */
export function getSectorsRotation(sector) {
  const params = sector ? { sector } : null;
  return get('/api/v1/sectors/rotation', params);
}

/** 龙头/二线筛选：GET /api/v1/stocks/leaders?type=first-line|second-line&sector=AI */
export function getStocksLeaders({ type, sector } = {}) {
  const params = { type };
  if (sector) params.sector = sector;
  return get('/api/v1/stocks/leaders', params);
}

/** 入场信号评估：POST /api/v1/trades/signal
 * payload: {symbol, mode, intraday?, ohlcv?, price?}
 */
export function postTradeSignal(payload) {
  return post('/api/v1/trades/signal', payload);
}

/** 交易闸门评估：POST /api/v1/risk/evaluate
 * payload: {symbol, sector?, price?}
 */
export function postRiskEvaluate(payload) {
  return post('/api/v1/risk/evaluate', payload);
}

/** 仓位建议：POST /api/v1/risk/position
 * payload: {symbol, sector?, account_size, price?}
 */
export function postRiskPosition(payload) {
  return post('/api/v1/risk/position', payload);
}

/** 撤退剧本：POST /api/v1/risk/exit-plan
 * payload: {symbol, sector?, entry, stop}
 */
export function postRiskExitPlan(payload) {
  return post('/api/v1/risk/exit-plan', payload);
}

/** 纸上交易-开仓：POST /api/v1/paper/open
 * payload: {symbol, sector?, mode, price?, account_size?}
 */
export function postPaperOpen(payload) {
  return post('/api/v1/paper/open', payload);
}

/** 纸上交易-推进：POST /api/v1/paper/step
 * payload: {price, high?, low?}
 */
export function postPaperStep(payload) {
  return post('/api/v1/paper/step', payload);
}

/** 纸上交易-状态：GET /api/v1/paper/state */
export function getPaperState() {
  return get('/api/v1/paper/state');
}

// —— 默认导出一个聚合对象（方便以 m.default 或 window.api 方式使用）——
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

// 可选：在浏览器环境挂到 window 便于调试（不影响模块导入）。
if (typeof window !== 'undefined') {
  window.api = api;
}
