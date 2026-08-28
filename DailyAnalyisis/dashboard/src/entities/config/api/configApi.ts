import { apiGet, apiPost, extractData } from "../../../shared/api/bridge";
import { PluginConfigData } from "../model/types";

export interface WebUIAuthStatus {
  configured: boolean;
  authenticated: boolean;
}

async function authRequest(
  action: string,
  body?: Record<string, unknown>
): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/daily_analyisis/auth/${action}`, {
    method: body ? "POST" : "GET",
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = (await response.json()) as Record<string, unknown>;
  if (!response.ok) {
    throw new Error(String(payload.message || `HTTP ${response.status}`));
  }
  return payload;
}

export async function fetchWebUIAuthStatus(): Promise<WebUIAuthStatus> {
  const payload = await authRequest("status");
  const data = (payload.data || {}) as Record<string, unknown>;
  return {
    configured: Boolean(data.configured),
    authenticated: Boolean(data.authenticated),
  };
}

export async function setupWebUIPassword(
  password: string,
  confirmation: string
): Promise<void> {
  await authRequest("setup", { password, confirmation });
}

export async function loginWebUI(password: string): Promise<void> {
  await authRequest("login", { password });
}

export interface AvailableProvider {
  id: string;
  name: string;
  type?: string;
  label?: string;
}

export interface AvailablePersona {
  id: string;
  name: string;
  label?: string;
}

export async function fetchPluginConfig(): Promise<PluginConfigData | null> {
  const res = await apiGet<PluginConfigData>("config");
  const data = extractData<PluginConfigData>(res);
  if (data && typeof data === "object") {
    if ("config" in data || "schema" in data) {
      return data;
    }
    const raw = data as Record<string, unknown>;
    if (raw.data && typeof raw.data === "object") {
      return raw.data as PluginConfigData;
    }
    return data;
  }
  return null;
}

export async function fetchAvailableProviders(): Promise<AvailableProvider[]> {
  const res = await apiGet<AvailableProvider[]>("providers");
  const data = extractData<AvailableProvider[]>(res);
  if (Array.isArray(data)) return data;
  return [];
}

export async function fetchAvailablePersonas(): Promise<AvailablePersona[]> {
  const res = await apiGet<AvailablePersona[]>("personas");
  const data = extractData<AvailablePersona[]>(res);
  if (Array.isArray(data)) return data;
  return [];
}

export async function savePluginConfig(
  config: Record<string, unknown>
): Promise<{ success: boolean; message?: string }> {
  try {
    const res = await apiPost("config", { config });
    if (res !== null && res !== undefined) {
      const raw = res as Record<string, unknown>;
      // 只有在明确返回 error 状态时才判定为失败
      if (
        raw.status === "error" ||
        raw.error ||
        (typeof raw.code === "number" && raw.code !== 0 && raw.code !== 200)
      ) {
        const errMsg =
          (raw.message as string) || (raw.error as string) || "保存配置失败";
        return { success: false, message: errMsg };
      }

      const msg =
        (raw.message as string) ||
        (typeof raw.data === "object" &&
          raw.data &&
          ((raw.data as Record<string, unknown>).message as string)) ||
        "配置已成功保存并持久化生效";

      return { success: true, message: msg };
    }
    return { success: false, message: "保存配置失败，未收到响应" };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, message: msg || "保存配置请求失败" };
  }
}
