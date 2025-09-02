// frontend/js/components/Card.js
// 简易卡片组件：渲染一个有边框的容器，可包含标题和内容。

export function Card({ title, content }) {
  const el = document.createElement('div');
  el.className = 'card';
  if (title) {
    const h = document.createElement('div');
    h.className = 'title';
    h.textContent = title;
    el.appendChild(h);
  }
  if (content instanceof Node) {
    el.appendChild(content);
  } else if (typeof content === 'string') {
    const p = document.createElement('div');
    p.innerHTML = content;
    el.appendChild(p);
  }
  return el;
}