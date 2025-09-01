// 事件总线（发布订阅）
const listeners = new Map();

export function on(evt, fn) {
  if (!listeners.has(evt)) listeners.set(evt, new Set());
  listeners.get(evt).add(fn);
  return () => off(evt, fn);
}
export function off(evt, fn) {
  const set = listeners.get(evt); if (!set) return;
  set.delete(fn);
}
export function emit(evt, payload) {
  const set = listeners.get(evt); if (!set) return;
  for (const fn of set) try { fn(payload); } catch (e) { console.error(e); }
}
