// 常用格式化工具
export const fmt = {
  pct(x, digits = 2) { return (x * 100).toFixed(digits) + "%"; },
  num(x, digits = 2) { return Number(x).toFixed(digits); },
  date(d) { return new Date(d).toLocaleDateString(); },
};
