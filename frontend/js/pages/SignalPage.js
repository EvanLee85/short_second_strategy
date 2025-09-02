// frontend/js/pages/SignalPage.js
// 入场信号页面：输入股票代码和模式，调用 /api/v1/trades/signal 来评估入场信号。

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { postTradeSignal } from '../api/endpoints.js';

export default {
  route: '/signal',
  title: '入场信号',
  render() {
    const container = document.createElement('div');
    // 构建表单
    const formCard = Card({ title: '入场信号评估', content: '' });
    const form = document.createElement('div');
    form.style.display = 'flex';
    form.style.flexWrap = 'wrap';
    form.style.gap = '8px';

    const symbolInput = document.createElement('input');
    symbolInput.type = 'text';
    symbolInput.placeholder = '股票代码，如 000001.SZ';
    symbolInput.className = 'input';

    const modeSelect = document.createElement('select');
    modeSelect.className = 'input';
    const modes = [
      { value: 'breakthrough', text: '突破' },
      { value: 'retracement', text: '回踩' },
      { value: 'reversal', text: '反转' },
    ];
    modes.forEach(({ value, text }) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = text;
      modeSelect.appendChild(opt);
    });

    const priceInput = document.createElement('input');
    priceInput.type = 'number';
    priceInput.placeholder = '可选：现价（留空则自动获取）';
    priceInput.className = 'input';
    priceInput.step = '0.01';

    const intradayCheckbox = document.createElement('label');
    intradayCheckbox.style.display = 'flex';
    intradayCheckbox.style.alignItems = 'center';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.style.marginRight = '4px';
    const cbText = document.createTextNode('日内模式');
    intradayCheckbox.appendChild(cb);
    intradayCheckbox.appendChild(cbText);

    const btn = document.createElement('button');
    btn.className = 'btn primary';
    btn.textContent = '评估入场';

    form.appendChild(symbolInput);
    form.appendChild(modeSelect);
    form.appendChild(priceInput);
    form.appendChild(intradayCheckbox);
    form.appendChild(btn);
    formCard.appendChild(form);

    const resultCard = Card({ title: '评估结果', content: '请提交表单' });

    container.appendChild(formCard);
    container.appendChild(resultCard);

    btn.addEventListener('click', async () => {
      const symbol = symbolInput.value.trim();
      if (!symbol) {
        toast('请输入股票代码', 'err');
        return;
      }
      const mode = modeSelect.value;
      const price = priceInput.value ? parseFloat(priceInput.value) : undefined;
      const intraday = cb.checked || undefined;
      const payload = { symbol, mode };
      if (price !== undefined && !Number.isNaN(price)) payload.price = price;
      if (intraday) payload.intraday = true;

      resultCard.innerHTML = '';
      resultCard.appendChild(Loading('正在评估入场信号…'));
      try {
        const res = await postTradeSignal(payload);
        if (!res.ok) throw res.error || new Error('请求失败');
        const data = res.data;
        const pre = document.createElement('pre');
        pre.style.whiteSpace = 'pre-wrap';
        pre.style.wordBreak = 'break-all';
        pre.textContent = JSON.stringify(data, null, 2);
        resultCard.innerHTML = '';
        resultCard.appendChild(
          Card({ title: '入场信号评估结果', content: pre })
        );
        toast('入场评估完成', 'ok');
      } catch (err) {
        resultCard.innerHTML = '';
        const errDiv = document.createElement('div');
        errDiv.innerHTML = `<p>评估失败。</p><p>${err.message || err}</p>`;
        resultCard.appendChild(Card({ title: '错误', content: errDiv }));
        toast('评估失败', 'err');
      }
    });

    return container;
  },
};