// frontend/js/pages/HealthPage.js
// 系统健康页面：检测后端服务是否可用，并展示返回结果。

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { getHealth } from '../api/endpoints.js';
import { CONFIG } from '../config.js';

export default {
  route: '/health',
  title: '系统健康',
  render() {
    const container = document.createElement('div');
    // 显示接口基础地址
    container.appendChild(
      Card({
        title: '连接信息',
        content: `接口地址： ${CONFIG.API_BASE}<br/>说明：用于检测后端 /api/v1/health 是否可达`,
      })
    );
    // 内容卡片
    const contentCard = Card({ title: '健康检查', content: Loading('正在请求 …') });
    container.appendChild(contentCard);
    // 加载并渲染
    (async () => {
      const t0 = performance.now();
      try {
        const res = await getHealth();
        const dt = Math.max(1, Math.round(performance.now() - t0));
        if (!res.ok) throw res.error || new Error('请求失败');
        const data = res.data || {};
        const wrap = document.createElement('div');
        const status = document.createElement('div');
        status.className = 'kv';
        status.innerHTML = `状态： ${res.status ?? '未知'} 　耗时： ${dt}ms`;
        const pre = document.createElement('pre');
        pre.style.marginTop = '8px';
        pre.style.whiteSpace = 'pre-wrap';
        pre.style.wordBreak = 'break-all';
        pre.textContent = JSON.stringify(data, null, 2);
        wrap.appendChild(status);
        wrap.appendChild(pre);
        contentCard.innerHTML = '';
        contentCard.appendChild(
          Card({ title: '健康检查（返回原文）', content: wrap })
        );
        toast('后端健康检查成功', 'ok');
      } catch (err) {
        const errBox = document.createElement('div');
        errBox.innerHTML = `请求失败，请确认后端是否已运行在 ${CONFIG.API_BASE}<br/>错误信息： ${err.message || err}`;
        contentCard.innerHTML = '';
        contentCard.appendChild(
          Card({ title: '健康检查失败', content: errBox })
        );
        toast('健康检查失败', 'err');
      }
    })();
    return container;
  },
};