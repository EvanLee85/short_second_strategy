// frontend/js/api/http.js
// 统一 HTTP 封装：超时 / 重试 / 错误码解析；统一返回 { ok, data, error }。
// 使用方式：import { request, get, post, setApiBase } from './http.js'

/** 读取 / 设置基础地址的策略：
 *  1) window.__API_BASE__（若页面运行时动态注入）
 *  2) <meta name="api-base" content="http://127.0.0.1:5000">
 *  3) 默认同源（相对路径）
 */
let __API_BASE__ = (() => {
  if (typeof window !== 'undefined' && window.__API_BASE__) return window.__API_BASE__;
  const meta = typeof document !== 'undefined' ? document.querySelector('meta[name="api-base"]') : null;
  if (meta && meta.content) return meta.content.trim().replace(/\/+$/, '');
  return ''; // 同源
})();

/** 允许在运行时切换 API 基地址 */
export function setApiBase(base) {
  __API_BASE__ = (base || '').trim().replace(/\/+$/, '');
}

const DEFAULT_TIMEOUT_MS = 10000; // 默认 10 秒超时
const DEFAULT_RETRIES = 1;        // 默认 1 次重试（共请求 2 次）
const RETRY_BACKOFF_BASE = 400;   // 指数退避基数（毫秒），如 400, 800, 1600...

/** 构造查询字符串（忽略 undefined / null / NaN / 空字符串） */
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

/** 睡眠（用于重试退避） */
function sleep(ms) {
  return new Promise(res => setTimeout(res, ms));
}

/** 解析响应体（优先按 JSON） */
async function parseResponseBody(resp) {
  const ctype = resp.headers.get('content-type') || '';
  if (ctype.includes('application/json')) {
    try {
      return await resp.json();
    } catch (e) {
      // JSON 解析失败，降级为文本
    }
  }
  try {
    return await resp.text();
  } catch {
    return null;
  }
}

/** 统一底层请求（带超时 + 重试） */
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
        // 成功：归一返回
        return { ok: true, data: payload, error: null, status: resp.status };
      }

      // 非 2xx：构造统一错误对象
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

      // 5xx 或 429 可重试，其它直接返回
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

      // 超时或网络错误，可按策略重试
      if (attempt < retries) {
        const backoff = RETRY_BACKOFF_BASE * Math.pow(2, attempt);
        await sleep(backoff);
        attempt += 1;
        continue;
      }

      // 构造网络层统一错误
      const errObj = {
        message: err && err.name === 'AbortError' ? '请求超时' : (err && err.message) || '网络错误',
        status: null,
        code: 'NETWORK_ERROR',
        details: null,
      };
      return { ok: false, data: null, error: errObj, status: null };
    }
  }

  // 理论上不会走到这里
  return {
    ok: false,
    data: null,
    error: { message: (lastError && lastError.message) || '未知错误', status: null, code: 'UNKNOWN', details: null },
    status: null,
  };
}

/** 统一请求入口
 * @param {Object} options
 * @param {'GET'|'POST'|'PUT'|'PATCH'|'DELETE'} options.method - HTTP 方法
 * @param {string} options.path - 相对路径（会自动拼到 __API_BASE__ 后）
 * @param {Object} [options.params] - 查询参数
 * @param {any} [options.body] - 请求体（对象将自动 JSON.stringify）
 * @param {Object} [options.headers] - 额外请求头
 * @param {number} [options.timeout] - 超时毫秒
 * @param {number} [options.retries] - 重试次数
 * @returns {Promise<{ok:boolean, data:any, error?:{message:string,status:number|null,code?:string,details?:any}, status:number|null}>}
 */
export async function request({
  method = 'GET',
  path = '/',
  params = null,
  body = undefined,
  headers = {},
  timeout = DEFAULT_TIMEOUT_MS,
  retries = DEFAULT_RETRIES,
} = {}) {
  const url = __API_BASE__ + path + buildQuery(params);

  const finalHeaders = new Headers(headers || {});
  // 自动设置 JSON
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
    finalHeaders.set('Accept', 'application/json, text/plain;q=0.9,*/*;q=0.8');
  }

  return rawFetch({
    method,
    url,
    body: finalBody,
    headers: finalHeaders,
    timeout,
    retries,
  });
}

/** 便捷 GET */
export function get(path, params, opts = {}) {
  return request({ method: 'GET', path, params, ...opts });
}

/** 便捷 POST */
export function post(path, body, opts = {}) {
  return request({ method: 'POST', path, body, ...opts });
}
