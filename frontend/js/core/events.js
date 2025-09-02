// js/core/events.js

export const EV = {
  MACRO_UPDATED: 'macroUpdated',
  PAPER_UPDATED: 'paperUpdated',
  SECTOR_UPDATED: 'sectorUpdated',
  LEADERS_UPDATED: 'leadersUpdated',
  SIGNAL_UPDATED: 'signalUpdated',
  RISK_UPDATED: 'riskUpdated',
};

// 发布事件
export function publish(event, data) {
  const eventObj = new CustomEvent(event, { detail: data });
  window.dispatchEvent(eventObj);
}

// 订阅事件
export function subscribe(event, callback) {
  window.addEventListener(event, (e) => callback(e.detail));
}
