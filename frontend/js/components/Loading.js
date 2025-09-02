// frontend/js/components/Loading.js
// 加载占位组件：显示一个简单的卡片和文本

export function Loading(text = '加载中…') {
  const el = document.createElement('div');
  el.className = 'card';
  el.textContent = text;
  return el;
}