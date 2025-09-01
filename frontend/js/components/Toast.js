// 右下角提示
let holder;
export function toast(msg, type = "ok", timeout = 2200) {
  if (!holder) { holder = document.createElement("div"); holder.className="toast"; document.body.appendChild(holder); }
  holder.className = `toast ${type === "err" ? "err" : "ok"}`;
  holder.textContent = msg;
  holder.style.opacity = "1";
  setTimeout(() => holder && (holder.style.opacity = "0"), timeout);
}
