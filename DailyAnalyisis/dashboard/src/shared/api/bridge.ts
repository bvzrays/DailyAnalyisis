/** GsCore WebUI REST 与 SSE 通信层。 */

export interface ApiResponse<T = unknown> {
  status?: string;
  data?: T;
  message?: string;
  items?: T extends Array<infer U> ? U[] : unknown[];
  total?: number;
  [key: string]: unknown;
}

const GSCORE_API_PREFIX = "/api/daily_analyisis/";

function apiUrl(path: string): string {
  return `${GSCORE_API_PREFIX}${path.replace(/^\/+/, "")}`;
}

export async function apiGet<T = unknown>(
  path: string,
  params?: Record<string, unknown>
): Promise<ApiResponse<T> | null> {
  const url = new URL(apiUrl(path), window.location.origin);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  const response = await fetch(url, { credentials: "same-origin" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as ApiResponse<T>;
}

export async function apiPost<T = unknown>(
  path: string,
  body?: unknown
): Promise<ApiResponse<T> | null> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as ApiResponse<T>;
}

export function subscribeSSE(handlers: {
  onMessage: (event: unknown) => void;
  onError?: () => void;
}): (() => void) | null {
  const source = new EventSource(apiUrl("events/stream"), { withCredentials: true });
  source.onmessage = (event) => {
    try {
      handlers.onMessage(JSON.parse(event.data));
    } catch {
      handlers.onMessage(event.data);
    }
  };
  source.onerror = () => handlers.onError?.();
  return () => source.close();
}

/**
 * 解包 GsCore 插件 Web API 返回的数据结构。
 */
export function extractData<T>(res: unknown): T | null {
  if (!res || typeof res !== "object") return null;
  const anyRes = res as Record<string, unknown>;

  // 1. 兼容历史数据中的深层响应封装。
  if (
    anyRes.data &&
    typeof anyRes.data === "object" &&
    "data" in (anyRes.data as Record<string, unknown>)
  ) {
    return (anyRes.data as Record<string, unknown>).data as T;
  }

  // 2. 单层解包：res.data
  if (anyRes.data !== undefined) {
    return anyRes.data as T;
  }

  // 3. 顶层对象
  return anyRes as unknown as T;
}
