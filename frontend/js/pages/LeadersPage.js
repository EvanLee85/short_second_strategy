// frontend/js/pages/LeadersPage.js
// 龙头筛选页面：选择一线或二线龙头以及可选板块，调用 /api/v1/stocks/leaders

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { getStocksLeaders } from '../api/endpoints.js';

export default {
  route: '/leaders',
  title: '龙头筛选',
  render() {
    const container = document.createElement('div');
    // 表单：选择 type 和 sector
    const formCard = Card({ title: '查询龙头股票', content: '' });
    const form = document.createElement('div');
    form.style.display = 'flex';
    form.style.flexWrap = 'wrap';
    form.style.gap = '8px';

    // type 选择
    const typeSelect = document.createElement('select');
    typeSelect.className = 'input';
    const opt1 = document.createElement('option'); opt1.value = 'first-line'; opt1.textContent = '一线龙头';
    const opt2 = document.createElement('option'); opt2.value = 'second-line'; opt2.textContent = '二线龙头';
    typeSelect.appendChild(opt1);
    typeSelect.appendChild(opt2);
    // sector 输入
    const sectorInput = document.createElement('input');
    sectorInput.type = 'text';
    sectorInput.placeholder = '可选：板块名称/代码';
    sectorInput.className = 'input';
    // 查询按钮
    const btn = document.createElement('button');
    btn.className = 'btn primary';
    btn.textContent = '查询';

    form.appendChild(typeSelect);
    form.appendChild(sectorInput);
    form.appendChild(btn);
    formCard.appendChild(form);

    // 结果卡片
    const resultCard = Card({ title: '龙头股票列表', content: '请先查询' });

    container.appendChild(formCard);
    container.appendChild(resultCard);

    btn.addEventListener('click', async () => {
      const type = typeSelect.value;
      const sector = sectorInput.value.trim() || undefined;
      resultCard.innerHTML = '';
      resultCard.appendChild(Loading('正在加载龙头股票…'));
      try {
        const res = await getStocksLeaders({ type, sector });
        if (!res.ok) throw res.error || new Error('请求失败');
        const stocks = Array.isArray(res.data) ? res.data : res.data?.stocks || res.data?.data || [];
        if (!Array.isArray(stocks) || stocks.length === 0) {
          resultCard.innerHTML = '';
          resultCard.appendChild(
            Card({ title: '无结果', content: `未找到符合条件的 ${type === 'first-line' ? '一线' : '二线'}龙头股票` })
          );
          toast('未找到符合条件的股票', 'ok');
          return;
        }
        // 构建表格
        const table = document.createElement('table');
        table.className = 'table';
        table.innerHTML = '<thead><tr><th>代码</th><th>名称</th><th>涨跌幅</th></tr></thead>';
        const tbody = document.createElement('tbody');
        stocks.forEach((item) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${item.symbol || item.code || ''}</td><td>${item.name || ''}</td><td>${item.pct_change ?? ''}</td>`;
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        resultCard.innerHTML = '';
        resultCard.appendChild(
          Card({ title: `${typeSelect.selectedOptions[0].text}股票列表`, content: table })
        );
        toast('龙头股票加载成功', 'ok');
      } catch (err) {
        resultCard.innerHTML = '';
        const errDiv = document.createElement('div');
        errDiv.innerHTML = `<p>加载龙头股票失败。</p><p>${err.message || err}</p>`;
        resultCard.appendChild(Card({ title: '错误', content: errDiv }));
        toast('加载龙头股票失败', 'err');
      }
    });

    return container;
  },
};