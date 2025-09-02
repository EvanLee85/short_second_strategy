// frontend/js/app.js
// 应用入口与简单路由控制。
// 负责根据 hash 路由加载相应页面模块，并渲染到 #app 容器。

import MacroPage from './pages/MacroPage.js';
import SectorsPage from './pages/SectorsPage.js';
import LeadersPage from './pages/LeadersPage.js';
import SignalPage from './pages/SignalPage.js';
import RiskPage from './pages/RiskPage.js';
import PaperPage from './pages/PaperPage.js';
import HealthPage from './pages/HealthPage.js';

/**
 * 简易路由表：根据 URL hash 映射到页面对象。
 * 每个页面对象定义 route、title 和 render() 方法。
 */
const routes = {
  '/health': HealthPage,
  '/macro': MacroPage,
  '/sectors': SectorsPage,
  '/leaders': LeadersPage,
  '/signal': SignalPage,
  '/risk': RiskPage,
  '/paper': PaperPage,
};

/**
 * 根据当前 location.hash 解析路由路径。
 * 默认路由为 '/health'。
 */
function getCurrentRoute() {
  const hash = window.location.hash || '';
  const match = hash.match(/^#(\/[^?]*)/);
  return (match && match[1]) || '/health';
}

/**
 * 更新导航栏 active 状态。
 * 根据当前路由为 nav a 标签添加或移除 'active' class。
 */
function updateNavActive(current) {
  const navLinks = document.querySelectorAll('header.nav a, header .nav a');
  navLinks.forEach((a) => {
    const href = a.getAttribute('href') || '';
    const route = href.replace(/^#/, '');
    a.classList.toggle('active', route === current);
  });
}

/**
 * 主渲染函数：加载并渲染当前路由对应页面。
 * 该函数在 hashchange 和 DOMContentLoaded 事件触发时调用。
 */
export function render() {
  const route = getCurrentRoute();
  const page = routes[route] || routes['/health'];
  // 更新文档标题
  if (page.title) {
    document.title = page.title + ' - short_second_strategy 控制台';
  }
  // 更新导航 active
  updateNavActive(route);
  // 渲染页面内容
  const appEl = document.getElementById('app');
  if (!appEl) return;
  // 清空容器
  appEl.innerHTML = '';
  try {
    const view = page.render();
    if (view instanceof Node) {
      appEl.appendChild(view);
    }
  } catch (err) {
    // 渲染异常：显示错误信息
    const errBox = document.createElement('pre');
    errBox.className = 'card';
    errBox.style.color = 'red';
    errBox.textContent = `渲染页面时发生错误：${err.message || err}`;
    appEl.appendChild(errBox);
    console.error(err);
  }
}

// 默认导出一个 init 函数（可选）
export default function init() {
  render();
}