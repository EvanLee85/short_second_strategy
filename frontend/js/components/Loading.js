// 加载占位
export function Loading(text = "加载中…") {
  const el = document.createElement("div");
  el.className = "card";
  el.textContent = text;
  return el;
}
