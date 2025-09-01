// 极简全局状态管理（仅占位，后续可扩展持久化/模块化）
export const store = {
  state: {
    // 示例：用户设置、当前路由、最近一次 API 响应等
    route: "/health",
    lastError: null,
    settings: { sector: "AI" },
  },
  set(k, v) { this.state[k] = v; },
  get(k) { return this.state[k]; },
};
