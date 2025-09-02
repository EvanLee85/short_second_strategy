// frontend/js/pages/RiskPage.js
// 风控评估页面：提供交易闸门评估、仓位建议、撤退计划三种功能。
// 每个功能对应后端 /api/v1/risk/* 路由。

import { Card } from '../components/Card.js';
import { Loading } from '../components/Loading.js';
import { toast } from '../components/Toast.js';
import { postRiskEvaluate, postRiskPosition, postRiskExitPlan } from '../api/endpoints.js';

export default {
  route: '/risk',
  title: '风险评估',
  render() {
    const container = document.createElement('div');

    /* ======== 闸门评估 ======== */
    const evalCard = Card({ title: '交易闸门评估', content: '' });
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
      const price = document.createElement('input');
      price.placeholder = '可选：现价';
      price.type = 'number';
      price.step = '0.01';
      price.className = 'input';
      const btn = document.createElement('button');
      btn.className = 'btn primary';
      btn.textContent = '评估闸门';
      const resultArea = document.createElement('div');
      resultArea.style.marginTop = '8px';

      form.appendChild(symbol);
      form.appendChild(sector);
      form.appendChild(price);
      form.appendChild(btn);
      evalCard.appendChild(form);
      evalCard.appendChild(resultArea);

      btn.addEventListener('click', async () => {
        const payload = {};
        if (symbol.value.trim()) payload.symbol = symbol.value.trim();
        else {
          toast('请填写股票代码', 'err');
          return;
        }
        if (sector.value.trim()) payload.sector = sector.value.trim();
        if (price.value) payload.price = parseFloat(price.value);
        resultArea.innerHTML = '';
        resultArea.appendChild(Loading('评估中…'));
        try {
          const res = await postRiskEvaluate(payload);
          if (!res.ok) throw res.error || new Error('请求失败');
          const pre = document.createElement('pre');
          pre.style.whiteSpace = 'pre-wrap';
          pre.style.wordBreak = 'break-all';
          pre.textContent = JSON.stringify(res.data, null, 2);
          resultArea.innerHTML = '';
          resultArea.appendChild(Card({ title: '闸门评估结果', content: pre }));
          toast('闸门评估完成', 'ok');
        } catch (err) {
          resultArea.innerHTML = '';
          const errDiv = document.createElement('div');
          errDiv.innerHTML = `<p>评估失败。</p><p>${err.message || err}</p>`;
          resultArea.appendChild(Card({ title: '错误', content: errDiv }));
          toast('评估失败', 'err');
        }
      });
    }

    /* ======== 仓位建议 ======== */
    const posCard = Card({ title: '仓位建议', content: '' });
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
      const account = document.createElement('input');
      account.placeholder = '账户资金 (必填)';
      account.type = 'number';
      account.step = '0.01';
      account.className = 'input';
      const price = document.createElement('input');
      price.placeholder = '可选：现价';
      price.type = 'number';
      price.step = '0.01';
      price.className = 'input';
      const btn = document.createElement('button');
      btn.className = 'btn primary';
      btn.textContent = '建议仓位';
      const resultArea = document.createElement('div');
      resultArea.style.marginTop = '8px';

      form.appendChild(symbol);
      form.appendChild(sector);
      form.appendChild(account);
      form.appendChild(price);
      form.appendChild(btn);
      posCard.appendChild(form);
      posCard.appendChild(resultArea);
      btn.addEventListener('click', async () => {
        const payload = {};
        if (!symbol.value.trim()) {
          toast('请填写股票代码', 'err');
          return;
        }
        payload.symbol = symbol.value.trim();
        if (sector.value.trim()) payload.sector = sector.value.trim();
        if (!account.value) {
          toast('请填写账户资金', 'err');
          return;
        }
        payload.account_size = parseFloat(account.value);
        if (price.value) payload.price = parseFloat(price.value);
        resultArea.innerHTML = '';
        resultArea.appendChild(Loading('计算中…'));
        try {
          const res = await postRiskPosition(payload);
          if (!res.ok) throw res.error || new Error('请求失败');
          const pre = document.createElement('pre');
          pre.style.whiteSpace = 'pre-wrap';
          pre.style.wordBreak = 'break-all';
          pre.textContent = JSON.stringify(res.data, null, 2);
          resultArea.innerHTML = '';
          resultArea.appendChild(Card({ title: '仓位建议结果', content: pre }));
          toast('仓位建议完成', 'ok');
        } catch (err) {
          resultArea.innerHTML = '';
          const errDiv = document.createElement('div');
          errDiv.innerHTML = `<p>计算失败。</p><p>${err.message || err}</p>`;
          resultArea.appendChild(Card({ title: '错误', content: errDiv }));
          toast('计算失败', 'err');
        }
      });
    }

    /* ======== 撤退计划 ======== */
    const exitCard = Card({ title: '撤退计划', content: '' });
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
      const entry = document.createElement('input');
      entry.placeholder = '入场价 (必填)';
      entry.type = 'number';
      entry.step = '0.01';
      entry.className = 'input';
      const stop = document.createElement('input');
      stop.placeholder = '止损价 (必填)';
      stop.type = 'number';
      stop.step = '0.01';
      stop.className = 'input';
      const btn = document.createElement('button');
      btn.className = 'btn primary';
      btn.textContent = '生成撤退计划';
      const resultArea = document.createElement('div');
      resultArea.style.marginTop = '8px';

      form.appendChild(symbol);
      form.appendChild(sector);
      form.appendChild(entry);
      form.appendChild(stop);
      form.appendChild(btn);
      exitCard.appendChild(form);
      exitCard.appendChild(resultArea);
      btn.addEventListener('click', async () => {
        if (!symbol.value.trim()) {
          toast('请填写股票代码', 'err');
          return;
        }
        if (!entry.value || !stop.value) {
          toast('请填写入场价与止损价', 'err');
          return;
        }
        const payload = {
          symbol: symbol.value.trim(),
          entry: parseFloat(entry.value),
          stop: parseFloat(stop.value),
        };
        if (sector.value.trim()) payload.sector = sector.value.trim();
        resultArea.innerHTML = '';
        resultArea.appendChild(Loading('生成撤退计划中…'));
        try {
          const res = await postRiskExitPlan(payload);
          if (!res.ok) throw res.error || new Error('请求失败');
          const pre = document.createElement('pre');
          pre.style.whiteSpace = 'pre-wrap';
          pre.style.wordBreak = 'break-all';
          pre.textContent = JSON.stringify(res.data, null, 2);
          resultArea.innerHTML = '';
          resultArea.appendChild(Card({ title: '撤退计划结果', content: pre }));
          toast('撤退计划生成完成', 'ok');
        } catch (err) {
          resultArea.innerHTML = '';
          const errDiv = document.createElement('div');
          errDiv.innerHTML = `<p>生成失败。</p><p>${err.message || err}</p>`;
          resultArea.appendChild(Card({ title: '错误', content: errDiv }));
          toast('生成撤退计划失败', 'err');
        }
      });
    }

    // 将三个卡片加入页面
    container.appendChild(evalCard);
    container.appendChild(posCard);
    container.appendChild(exitCard);
    return container;
  },
};