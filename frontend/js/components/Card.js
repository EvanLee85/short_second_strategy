// 卡片组件（最小化：仅容器）
export function Card({ title, content }) {
  const el = document.createElement("div");
  el.className = "card";
  if (title) {
    const h = document.createElement("div");
    h.className = "title";
    h.textContent = title;
    el.appendChild(h);
  }
  if (content instanceof Node) el.appendChild(content);
  else if (typeof content === "string") {
    const p = document.createElement("div"); p.innerHTML = content; el.appendChild(p);
  }
  return el;
}
