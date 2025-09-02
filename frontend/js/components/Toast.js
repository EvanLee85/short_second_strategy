// frontend/js/components/Toast.js
// 提示组件：显示一个右下角的提示信息，支持“ok”和“err”样式。

let holder;
export function toast(msg, type = 'ok', timeout = 2200) {
  if (!holder) {
    holder = document.createElement('div');
    holder.className = 'toast';
    document.body.appendChild(holder);
  }
  holder.className = `toast ${type === 'err' ? 'err' : 'ok'}`;
  holder.textContent = msg;
  holder.style.opacity = '1';
  setTimeout(() => {
    if (holder) holder.style.opacity = '0';
  }, timeout);
}