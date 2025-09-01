// /health 页面：调用后端 /api/v1/health 并展示结果（含耗时/错误提示）
// 中文注释说明：本页用于最小化验证“前端→后端”HTTP连通性。
// - 加载占位：Loading
// - 成功：状态 + 耗时 + 原始 JSON
// - 失败：Toast 提示 + 错误卡片

import { Card } from "../components/Card.js";
import { Loading } from "../components/Loading.js";
import { toast } from "../components/Toast.js";
import { api } from "../api/endpoints.js";
import { CONFIG } from "../config.js";

export default {
  route: "/health",
  title: "系统健康",
  render() {
    const box = document.createElement("div");

    // 顶部卡片：显示当前 API 根地址，便于排查环境问题
    box.appendChild(
      Card({
        title: "连接信息",
        content: `
          <div class="kv">接口地址：<strong>${CONFIG.API_BASE}</strong></div>
          <div class="kv">说明：用于检测后端 /api/v1/health 是否可达</div>
        `,
      })
    );

    // 内容卡片：先放加载占位
    const contentCard = Card({
      title: "健康检查",
      content: Loading("正在请求 /api/v1/health …"),
    });
    box.appendChild(contentCard);

    // 发起请求并渲染结果
    (async () => {
      const t0 = performance.now();
      try {
        const data = await api.health(); // GET /api/v1/health
        const ms = Math.max(1, Math.round(performance.now() - t0));

        // 构造展示节点（状态 + 耗时 + 原始JSON）
        const wrap = document.createElement("div");
        const status = document.createElement("div");
        status.className = "kv";
        status.innerHTML = `状态：<strong>${data.status ?? "未知"}</strong>　耗时：<strong>${ms}ms</strong>`;
        const raw = document.createElement("pre");
        raw.style.marginTop = "8px";
        raw.style.whiteSpace = "pre-wrap";
        raw.style.wordBreak = "break-all";
        raw.textContent = JSON.stringify(data, null, 2);

        wrap.appendChild(status);
        wrap.appendChild(raw);

        // 替换卡片内容
        contentCard.innerHTML = "";
        contentCard.appendChild(
          Card({
            title: "健康检查（返回原文）",
            content: wrap,
          })
        );

        toast("后端健康检查成功", "ok");
      } catch (err) {
        // 异常时的友好提示与错误信息
        console.error(err);
        toast(`健康检查失败：${err.message || err}`, "err");

        const errBox = document.createElement("div");
        errBox.innerHTML = `
          <div class="kv">请求失败，请确认后端是否已运行在 <strong>${CONFIG.API_BASE}</strong></div>
          <div class="kv">错误信息：<strong>${(err && err.message) || String(err)}</strong></div>
        `;

        contentCard.innerHTML = "";
        contentCard.appendChild(
          Card({
            title: "健康检查失败",
            content: errBox,
          })
        );
      }
    })();

    return box;
  },
};
