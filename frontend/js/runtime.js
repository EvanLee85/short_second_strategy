// 启动顺序控制：这里挂载路由监听与首次渲染
import { render } from "./app.js";

window.addEventListener("hashchange", () => render());
window.addEventListener("DOMContentLoaded", () => render());
