// frontend/js/pages/PaperPage.js
// 纸上交易页面：模拟交易接口，包括开仓、推进行情、查看状态。

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { postPaperOpen, postPaperStep, getPaperState } from '../api/endpoints.js';

export default {
  route: '/paper',
  title: '纸上交易',
  render() {
    const container = document.createElement('div');

    /* ==== 开仓 ==== */
    const openCard = Card({ title: '开仓', content: '' });
    {
      const form = document.createElement('div');
      form.style.display = 'flex';
      form.style.flexWrap = 'wrap';
      form.style.gap = '8px';
      const symbol = document.createElement('input');
      symbol.placeholder = '股票代码';
      symbol.className = 'input';
      const sector = document.createElement('input');
      sector.placeholder = '可选：板块';
      sector.className = 'input';
      const mode = document.createElement('select');
      mode.className = 'input';
      [
        { value: 'breakthrough', text: '突破' },
        { value: 'retracement', text: '回踩' },
        { value: 'reversal', text: '反转' },
      ].forEach(({ value, text }) => {
        const opt = document.createElement('option');
        opt.value = value; opt.textContent = text; mode.appendChild(opt);
      });
      const price = document.createElement('input');
      price.placeholder = '可选：现价';
      price.type = 'number'; price.step = '0.01'; price.className = 'input';
      const account = document.createElement('input');
      account.placeholder = '可选：账户资金';
      account.type = 'number'; account.step = '0.01'; account.className = 'input';
      const btn = document.createElement('button');
      btn.className = 'btn primary'; btn.textContent = '开仓';
      const resultArea = document.createElement('div'); resultArea.style.marginTop = '8px';

      form.appendChild(symbol);
      form.appendChild(sector);
      form.appendChild(mode);
      form.appendChild(price);
      form.appendChild(account);
      form.appendChild(btn);
      openCard.appendChild(form);
      openCard.appendChild(resultArea);
      btn.addEventListener('click', async () => {
        if (!symbol.value.trim()) { toast('请填写股票代码', 'err'); return; }
        const payload = { symbol: symbol.value.trim(), mode: mode.value };
        if (sector.value.trim()) payload.sector = sector.value.trim();
        if (price.value) payload.price = parseFloat(price.value);
        if (account.value) payload.account_size = parseFloat(account.value);
        resultArea.innerHTML = '';
        resultArea.appendChild(Loading('开仓中…'));
        try {
          const res = await postPaperOpen(payload);
          if (!res.ok) throw res.error || new Error('请求失败');
          const pre = document.createElement('pre');
          pre.style.whiteSpace = 'pre-wrap'; pre.style.wordBreak = 'break-all';
          pre.textContent = JSON.stringify(res.data, null, 2);
          resultArea.innerHTML = '';
          resultArea.appendChild(Card({ title: '开仓结果', content: pre }));
          toast('开仓成功', 'ok');
        } catch (err) {
          resultArea.innerHTML = '';
          const errDiv = document.createElement('div');
          errDiv.innerHTML = `<p>开仓失败。</p><p>${err.message || err}</p>`;
          resultArea.appendChild(Card({ title: '错误', content: errDiv }));
          toast('开仓失败', 'err');
        }
      });
    }

    /* ==== 推进行情（step） ==== */
    const stepCard = Card({ title: '推进行情', content: '' });
    {
      const form = document.createElement('div');
      form.style.display = 'flex';
      form.style.flexWrap = 'wrap';
      form.style.gap = '8px';
      const price = document.createElement('input');
      price.placeholder = '当前价 (必填)';
      price.type = 'number'; price.step = '0.01'; price.className = 'input';
      const high = document.createElement('input');
      high.placeholder = '可选：最高价';
      high.type = 'number'; high.step = '0.01'; high.className = 'input';
      const low = document.createElement('input');
      low.placeholder = '可选：最低价';
      low.type = 'number'; low.step = '0.01'; low.className = 'input';
      const btn = document.createElement('button');
      btn.className = 'btn primary';
      btn.textContent = '推进';
      const resultArea = document.createElement('div'); resultArea.style.marginTop = '8px';
      form.appendChild(price);
      form.appendChild(high);
      form.appendChild(low);
      form.appendChild(btn);
      stepCard.appendChild(form);
      stepCard.appendChild(resultArea);
      btn.addEventListener('click', async () => {
        if (!price.value) { toast('请填写当前价', 'err'); return; }
        const payload = { price: parseFloat(price.value) };
        if (high.value) payload.high = parseFloat(high.value);
        if (low.value) payload.low = parseFloat(low.value);
        resultArea.innerHTML = '';
        resultArea.appendChild(Loading('推进中…'));
        try {
          const res = await postPaperStep(payload);
          if (!res.ok) throw res.error || new Error('请求失败');
          const pre = document.createElement('pre'); pre.style.whiteSpace = 'pre-wrap'; pre.style.wordBreak = 'break-all';
          pre.textContent = JSON.stringify(res.data, null, 2);
          resultArea.innerHTML = '';
          resultArea.appendChild(Card({ title: '推进结果', content: pre }));
          toast('行情推进成功', 'ok');
        } catch (err) {
          resultArea.innerHTML = '';
          const errDiv = document.createElement('div'); errDiv.innerHTML = `<p>推进失败。</p><p>${err.message || err}</p>`;
          resultArea.appendChild(Card({ title: '错误', content: errDiv }));
          toast('推进失败', 'err');
        }
      });
    }

    /* ==== 状态查看 ==== */
    const stateCard = Card({ title: '查看当前交易状态', content: '' });
    {
      const form = document.createElement('div'); form.style.display = 'flex'; form.style.gap = '8px';
      const btn = document.createElement('button'); btn.className = 'btn primary'; btn.textContent = '获取状态';
      const resultArea = document.createElement('div'); resultArea.style.marginTop = '8px';
      form.appendChild(btn);
      stateCard.appendChild(form);
      stateCard.appendChild(resultArea);
      btn.addEventListener('click', async () => {
        resultArea.innerHTML = '';
        resultArea.appendChild(Loading('获取中…'));
        try {
          const res = await getPaperState();
          if (!res.ok) throw res.error || new Error('请求失败');
          const pre = document.createElement('pre'); pre.style.whiteSpace = 'pre-wrap'; pre.style.wordBreak = 'break-all';
          pre.textContent = JSON.stringify(res.data, null, 2);
          resultArea.innerHTML = '';
          resultArea.appendChild(Card({ title: '当前状态', content: pre }));
          toast('获取状态成功', 'ok');
        } catch (err) {
          resultArea.innerHTML = '';
          const errDiv = document.createElement('div'); errDiv.innerHTML = `<p>获取失败。</p><p>${err.message || err}</p>`;
          resultArea.appendChild(Card({ title: '错误', content: errDiv }));
          toast('获取状态失败', 'err');
        }
      });
    }

    container.appendChild(openCard);
    container.appendChild(stepCard);
    container.appendChild(stateCard);
    return container;
  },
};