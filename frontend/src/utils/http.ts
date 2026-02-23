export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export async function http<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase();
  const headers = new Headers(init.headers ?? {});
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json');

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCookie('csrf_token');
    if (csrf) headers.set('x-csrf-token', csrf);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  });

  if (!res.ok) {
    let detail = 'request_failed';
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function mapLimitDetail(detail: string): string {
  if (detail === 'minute_rate_limited') return 'Слишком часто. Попробуйте снова через минуту.';
  if (detail === 'daily_limit_exceeded') return 'Дневной лимит запросов исчерпан. Попробуйте завтра.';
  return 'Временное ограничение. Попробуйте позже.';
}
