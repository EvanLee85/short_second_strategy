// 简易 hash 路由：将路径映射到页面模块
import HealthPage from "./pages/HealthPage.js";
import MacroPage from "./pages/MacroPage.js";
import SectorsPage from "./pages/SectorsPage.js";
import LeadersPage from "./pages/LeadersPage.js";
import SignalPage from "./pages/SignalPage.js";
import RiskPage from "./pages/RiskPage.js";
import PaperPage from "./pages/PaperPage.js";
import NotFoundPage from "./pages/NotFoundPage.js";

export const routes = [
  HealthPage, MacroPage, SectorsPage, LeadersPage, SignalPage, RiskPage, PaperPage
];

export function resolveRoute() {
  // hash 形如 #/health
  const hash = location.hash || "#/health";
  const path = hash.replace(/^#/, "");
  return routes.find(r => r.route === path) || NotFoundPage;
}

export function render() {
  const app = document.getElementById("app");
  if (!app) return;
  app.innerHTML = "";
  const page = resolveRoute();
  document.title = page.title ? `${page.title} - SSS 控制台` : "SSS 控制台";
  app.appendChild(page.render());
}
