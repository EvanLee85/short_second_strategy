// 轻量 fetch 封装：统一超时/错误提示（后续可接入 Toast）

/** 超时控制 */
function withTimeout(promise, ms = 15000) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("请求超时")), ms);
    promise.then(
      (v) => { clearTimeout(t); resolve(v); },
      (e) => { clearTimeout(t); reject(e); }
    );
  });
}

export async function httpGet(url) {
  const resp = await withTimeout(fetch(url, { headers: { "Accept": "application/json" } }));
  if (!resp.ok) throw new Error(`GET ${url} ${resp.status}`);
  return resp.json();
}

export async function httpPost(url, body) {
  const resp = await withTimeout(fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(body || {})
  }));
  if (!resp.ok) throw new Error(`POST ${url} ${resp.status}`);
  return resp.json();
}
