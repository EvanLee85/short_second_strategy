// 迷你图占位（后续可引入轻量绘图或使用 <canvas> 原生绘制）
export function ChartMini() {
  const el = document.createElement("div");
  el.className = "card";
  el.textContent = "（迷你图占位）";
  return el;
}
