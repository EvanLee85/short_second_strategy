// js/core/store.js

class Store {
  constructor() {
    this.state = {
      health: null,
      macro: null,
      sectors: null,
      leaders: null,
      signal: null,
      risk: null,
      paperState: null,
      ui: {
        route: '',
        loading: false,
        toasts: [],
      }
    };
    this.subscribers = {}; // 存储所有订阅事件的回调函数
  }

  // 设置部分状态并通知订阅者
  setState(partial) {
    this.state = { ...this.state, ...partial };  // 更新状态
    Object.keys(partial).forEach(key => {
      if (this.subscribers[key]) {
        this.subscribers[key].forEach(cb => cb(this.state[key]));
      }
    });
  }

  // 订阅某个状态的变化
  subscribe(key, cb) {
    if (!this.subscribers[key]) {
      this.subscribers[key] = [];
    }
    this.subscribers[key].push(cb);
  }

  // 获取状态
  getState() {
    return this.state;
  }
}

const store = new Store();
export default store;
