// frontend/js/pages/MacroPage.js
// 宏观状态页面：显示市场整体宏观指标，如恐慌指数、期货涨跌幅、市场广度等。
// 调用后端 /api/v1/macro/status 并以卡片形式呈现。

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { getMacroStatus } from '../api/endpoints.js';

export default {
  route: '/macro',
  title: '宏观状态',
  render() {
    const container = document.createElement('div');
    // 标题卡片
    container.appendChild(
      Card({ title: '宏观市场状态', content: '正在请求宏观指标…' })
    );
    // 请求数据并更新
    (async () => {
      const box = container.firstChild;
      box.innerHTML = '';
      box.appendChild(Loading('正在加载宏观指标…'));
      try {
        const res = await getMacroStatus();
        if (!res.ok) throw res.error || new Error('请求失败');
        const data = res.data || {};
        // 构造列表显示 key-value
        const list = document.createElement('dl');
        list.style.lineHeight = '1.6';
        for (const [key, value] of Object.entries(data)) {
          const dt = document.createElement('dt');
          dt.style.fontWeight = 'bold';
          dt.textContent = key;
          const dd = document.createElement('dd');
          dd.style.marginLeft = '1em';
          dd.textContent = typeof value === 'object' ? JSON.stringify(value) : String(value);
          list.appendChild(dt);
          list.appendChild(dd);
        }
        box.innerHTML = '';
        box.appendChild(
          Card({
            title: '宏观市场状态',
            content: list,
          })
        );
        toast('宏观指标加载成功', 'ok');
      } catch (err) {
        box.innerHTML = '';
        const errDiv = document.createElement('div');
        errDiv.innerHTML = `<p>加载宏观指标失败。</p><p>${err.message || err}</p>`;
        box.appendChild(
          Card({ title: '错误', content: errDiv })
        );
        toast('宏观指标加载失败', 'err');
      }
    })();
    return container;
  },
};