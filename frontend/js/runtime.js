// frontend/js/runtime.js
// 启动程序：监听 hashchange 和 DOMContentLoaded 事件，调用 app.js 的 render()

import { render } from './app.js';

window.addEventListener('hashchange', () => {
  render();
});

window.addEventListener('DOMContentLoaded', () => {
  render();
});