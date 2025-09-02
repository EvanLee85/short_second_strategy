// frontend/js/api/http.js
// HTTP 请求封装：提供 request、get、post 等方法。
// 支持超时、重试以及统一的错误处理，返回 { ok, data, error, status }。

// 基础地址读取策略：优先使用 window.__API_BASE__，次之 HTML meta[name="api-base"], 最后同源相对路径
let __API_BASE__ = (() => {
  if (typeof window !== 'undefined' && window.__API_BASE__) return window.__API_BASE__;
  const meta = typeof document !== 'undefined' ? document.querySelector('meta[name="api-base"]') : null;
  if (meta && meta.content) return meta.content.trim().replace(/\/+$/, '');
  return '';
})();

// 允许在运行时设置 API 基地址
export function setApiBase(base) {
  __API_BASE__ = (base || '').trim().replace(/\/+$/, '');
}

const DEFAULT_TIMEOUT_MS = 10000;
const DEFAULT_RETRIES = 1;
const RETRY_BACKOFF_BASE = 400;

// 构造查询字符串
function buildQuery(params) {
  if (!params) return '';
  const q = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    if (typeof v === 'number' && Number.isNaN(v)) continue;
    if (typeof v === 'string' && v.trim() === '') continue;
    q.push(encodeURIComponent(k) + '=' + encodeURIComponent(String(v)));
  }
  return q.length ? `?${q.join('&')}` : '';
}

// 简单 sleep，用于退避等待
function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

// 解析响应体
async function parseResponseBody(resp) {
  const ctype = resp.headers.get('content-type') || '';
  if (ctype.includes('application/json')) {
    try {
      return await resp.json();
    } catch (e) {
      // fall through to text
    }
  }
  try {
    return await resp.text();
  } catch {
    return null;
  }
}

// 发起原始 fetch 请求（带超时 + 重试）
async function rawFetch({ method, url, body, headers, timeout, retries }) {
  let attempt = 0;
  let lastError = null;
  while (attempt <= retries) {
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), timeout);
    try {
      const resp = await fetch(url, {
        method,
        headers,
        body,
        signal: controller.signal,
        credentials: 'same-origin',
      });
      clearTimeout(to);
      const payload = await parseResponseBody(resp);
      if (resp.ok) {
        return { ok: true, data: payload, error: null, status: resp.status };
      }
      // 非 2xx
      const msg =
        (payload && payload.error && (payload.error.message || payload.error)) ||
        (payload && payload.message) ||
        (typeof payload === 'string' ? payload : '') ||
        `HTTP ${resp.status}`;
      const errObj = {
        message: String(msg),
        status: resp.status,
        code: (payload && payload.error && payload.error.code) || null,
        details: payload && payload.error && payload.error.details ? payload.error.details : null,
      };
      // 5xx 或 429 可重试
      if ((resp.status >= 500 || resp.status === 429) && attempt < retries) {
        const backoff = RETRY_BACKOFF_BASE * Math.pow(2, attempt);
        await sleep(backoff);
        attempt += 1;
        continue;
      }
      return { ok: false, data: null, error: errObj, status: resp.status };
    } catch (err) {
      clearTimeout(to);
      lastError = err;
      if (attempt < retries) {
        const backoff = RETRY_BACKOFF_BASE * Math.pow(2, attempt);
        await sleep(backoff);
        attempt += 1;
        continue;
      }
      return {
        ok: false,
        data: null,
        error: {
          message: err && err.name === 'AbortError' ? '请求超时' : (err && err.message) || '网络错误',
          status: null,
          code: 'NETWORK_ERROR',
          details: null,
        },
        status: null,
      };
    }
  }
  return {
    ok: false,
    data: null,
    error: { message: (lastError && lastError.message) || '未知错误', status: null, code: 'UNKNOWN', details: null },
    status: null,
  };
}

// 统一请求入口
export async function request({ method = 'GET', path = '/', params = null, body = undefined, headers = {}, timeout = DEFAULT_TIMEOUT_MS, retries = DEFAULT_RETRIES } = {}) {
  const url = __API_BASE__ + path + buildQuery(params);
  const finalHeaders = new Headers(headers || {});
  let finalBody = body;
  if (body !== undefined && body !== null) {
    if (typeof body === 'object' && !(body instanceof FormData)) {
      if (!finalHeaders.has('Content-Type')) {
        finalHeaders.set('Content-Type', 'application/json');
      }
      finalBody = JSON.stringify(body);
    }
  }
  if (!finalHeaders.has('Accept')) {
    finalHeaders.set('Accept', 'application/json');
  }
  return await rawFetch({ method, url, body: finalBody, headers: finalHeaders, timeout, retries });
}

// 简单封装 GET
export function get(path, params = null, options = {}) {
  return request({ method: 'GET', path, params, ...options });
}

// 简单封装 POST
export function post(path, body = undefined, options = {}) {
  return request({ method: 'POST', path, body, ...options });
}