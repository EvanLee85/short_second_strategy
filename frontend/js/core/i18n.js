// 预留多语言（当前仅中文）
const zh = {
  HEALTH: "系统健康",
  MACRO: "宏观状态",
  ROTATION: "行业轮动",
  LEADERS: "龙头筛选",
  SIGNAL: "入场信号",
  RISK: "风控评估",
  PAPER: "纸上交易",
  ERROR: "出错了",
};

export function t(key) { return zh[key] || key; }
