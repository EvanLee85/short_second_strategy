// 端点函数：与后端 /api/v1/* 对齐（仅签名，后续页面调用）
// 现有后端路由见你贴出的 url_map

import { CONFIG } from "../config.js";
import { httpGet, httpPost } from "./http.js";

const B = CONFIG.API_BASE;

export const api = {
  // 健康检查
  health: () => httpGet(`${B}/health`),

  // 宏观过滤器
  macroStatus: () => httpGet(`${B}/macro/status`),

  // 行业轮动
  sectorRotation: (sector) => {
    const q = sector ? `?sector=${encodeURIComponent(sector)}` : "";
    return httpGet(`${B}/sectors/rotation${q}`);
  },

  // 龙头筛选
  leaders: ({ type, sector } = {}) => {
    const params = new URLSearchParams();
    if (type) params.set("type", type);
    if (sector) params.set("sector", sector);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return httpGet(`${B}/stocks/leaders${qs}`);
  },

  // 入场信号
  tradeSignal: (payload) => httpPost(`${B}/trades/signal`, payload),

  // 风控：评估/仓位/剧本
  riskEvaluate: (payload) => httpPost(`${B}/risk/evaluate`, payload),
  riskPosition: (payload) => httpPost(`${B}/risk/position`, payload),
  riskExitPlan: (payload) => httpPost(`${B}/risk/exit-plan`, payload),

  // 纸上交易
  paperOpen: (payload) => httpPost(`${B}/paper/open`, payload),
  paperStep: (payload) => httpPost(`${B}/paper/step`, payload),
  paperState: () => httpGet(`${B}/paper/state`),
};
