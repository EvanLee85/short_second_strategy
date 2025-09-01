// frontend/js/app.js
// 说明：页面级入口。自动做健康检查，并把结果渲染到卡片；提供“重新检测”按钮（若页面里有该按钮）。

import { getHealth } from './api/endpoints.js?v=20250901'; // 带版本参数避免浏览器缓存旧文件

function qs(sel) { return document.querySelector(sel); }
function renderJSON(el, data) {
  try { el.textContent = JSON.stringify(data, null, 2); }
  catch { el.textContent = String(data); }
}

async function runHealth() {
  const statusEl  = qs('#health-status');
  const delayEl   = qs('#health-latency');
  const jsonEl    = qs('#health-json');
  const cardEl    = qs('#health-card'); // 若没有此元素，下面的 classList.toggle 会安全忽略

  // 初始化占位
  if (statusEl) statusEl.textContent = '...';
  if (delayEl)  delayEl.textContent  = '...';
  if (jsonEl)   jsonEl.textContent   = '';

  const t0 = performance.now();
  let res;
  try {
    res = await getHealth();
  } catch (err) {
    // 网络或 JS 异常
    if (statusEl) statusEl.textContent = 'fail';
    if (delayEl)  delayEl.textContent  = '-';
    if (jsonEl)   renderJSON(jsonEl, String(err));
    if (cardEl)   cardEl.classList.add('error');
    return;
  }

  const dt = Math.round(performance.now() - t0);
  const ok = !!(res && res.ok);

  if (statusEl) statusEl.textContent = ok ? 'ok' : 'fail';
  if (delayEl)  delayEl.textContent  = `${dt}ms`;
  if (jsonEl)   renderJSON(jsonEl, ok ? (res.data ?? {}) : (res.error ?? res));

  if (cardEl) cardEl.classList.toggle('error', !ok);
}

document.addEventListener('DOMContentLoaded', () => {
  runHealth(); // 页面加载即自检

  const retryBtn = qs('#btn-health-test'); // 若页面有“重新检测”按钮则绑定
  if (retryBtn) retryBtn.addEventListener('click', () => runHealth());
});
