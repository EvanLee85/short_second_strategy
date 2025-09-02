// frontend/js/pages/SectorsPage.js
// 行业轮动页面：根据输入的板块代码/名称，调用后端 /api/v1/sectors/rotation
// 返回该板块的轮动指标（强度、广度、时间延续性、资金集中度、背书事件、隐藏资金）
// 并展示板块的龙头和二线股票列表。

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { getSectorsRotation } from '../api/endpoints.js';

export default {
  route: '/sectors',
  title: '板块轮动',
  render() {
    const container = document.createElement('div');

    // 输入区
    const formCard = Card({
      title: '查询板块轮动',
      content: '',
    });
    const form = document.createElement('div');
    form.style.display = 'flex';
    form.style.flexWrap = 'wrap';
    form.style.gap = '8px';

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = '请输入板块名称或代码（例如 AI）';
    input.className = 'input';

    const btn = document.createElement('button');
    btn.textContent = '查询';
    btn.className = 'btn primary';

    form.appendChild(input);
    form.appendChild(btn);
    formCard.appendChild(form);

    // 结果区：先留空
    const resultCard = Card({ title: '轮动指标', content: '请先输入板块并查询' });

    container.appendChild(formCard);
    container.appendChild(resultCard);

    // 点击查询
    btn.addEventListener('click', async () => {
      const sector = input.value.trim() || null;
      resultCard.innerHTML = '';
      resultCard.appendChild(Loading('正在加载板块数据…'));
      try {
        const res = await getSectorsRotation(sector);
        if (!res.ok) throw res.error || new Error('请求失败');
        const data = res.data || {};
        // 构建结果列表
        const wrap = document.createElement('div');
        // 展示主指标
        const dl = document.createElement('dl');
        dl.style.lineHeight = '1.6';
        const simpleKeys = [
          'strength',
          'breadth',
          'time_continuation',
          'capital_ratio',
          'endorsements',
          'hidden_funds',
        ];
        for (const key of simpleKeys) {
          if (data[key] !== undefined) {
            const dt = document.createElement('dt');
            dt.textContent = key;
            const dd = document.createElement('dd');
            dd.style.marginLeft = '1em';
            const val = data[key];
            dd.textContent = typeof val === 'object' ? JSON.stringify(val) : String(val);
            dl.appendChild(dt);
            dl.appendChild(dd);
          }
        }
        wrap.appendChild(dl);
        // 展示龙头股票列表
        if (Array.isArray(data.top_stocks) && data.top_stocks.length) {
          const table = document.createElement('table');
          table.className = 'table';
          const thead = document.createElement('thead');
          thead.innerHTML = '<tr><th>龙头股票</th><th>名称</th><th>涨跌幅</th></tr>';
          table.appendChild(thead);
          const tbody = document.createElement('tbody');
          data.top_stocks.forEach((row) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${row.symbol}</td><td>${row.name ?? ''}</td><td>${row.pct_change ?? ''}</td>`;
            tbody.appendChild(tr);
          });
          table.appendChild(tbody);
          const heading = document.createElement('h3');
          heading.textContent = '龙头股票';
          wrap.appendChild(heading);
          wrap.appendChild(table);
        }
        // 展示二线股票列表
        if (Array.isArray(data.second_line_candidates) && data.second_line_candidates.length) {
          const table2 = document.createElement('table');
          table2.className = 'table';
          table2.innerHTML = '<thead><tr><th>二线股票</th><th>名称</th><th>涨跌幅</th></tr></thead>';
          const tbody2 = document.createElement('tbody');
          data.second_line_candidates.forEach((row) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${row.symbol}</td><td>${row.name ?? ''}</td><td>${row.pct_change ?? ''}</td>`;
            tbody2.appendChild(tr);
          });
          table2.appendChild(tbody2);
          const heading2 = document.createElement('h3');
          heading2.textContent = '二线候选股票';
          wrap.appendChild(heading2);
          wrap.appendChild(table2);
        }
        resultCard.innerHTML = '';
        resultCard.appendChild(
          Card({ title: `板块 ${sector || ''} 轮动指标`, content: wrap })
        );
        toast('板块数据加载成功', 'ok');
      } catch (err) {
        resultCard.innerHTML = '';
        const errDiv = document.createElement('div');
        errDiv.innerHTML = `<p>加载板块数据失败。</p><p>${err.message || err}</p>`;
        resultCard.appendChild(Card({ title: '错误', content: errDiv }));
        toast('加载板块数据失败', 'err');
      }
    });
    return container;
  },
};