// fetch 래퍼 (토큰 자동 첨부, 401 처리)
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export function setToken(token) {
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
}

export function getToken() {
    return localStorage.getItem('token');
}

export async function api(path, { method = 'GET', body, headers } = {}) {
    const token = getToken();
    const r = await fetch(`${BASE}${path}`, {
        method,
        headers: {
            ...(body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...headers
        },
        body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
        credentials: 'include'
    });
    if (r.status === 401) setToken(null);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json().catch(() => ({}));
}
