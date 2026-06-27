import { useAuthStore } from "@shared/store/authStore";
import type { TokenPair } from "@shared/types";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean; // varsayılan true: access token ekle
  _retry?: boolean;
}

async function parseError(res: Response): Promise<ApiError> {
  let detail: unknown = res.statusText;
  try {
    const data = await res.json();
    detail = (data as { detail?: unknown }).detail ?? data;
  } catch {
    /* gövde yok */
  }
  const message =
    typeof detail === "string" ? detail : `İstek başarısız (${res.status})`;
  return new ApiError(res.status, detail, message);
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const { refreshToken, setTokens, logout } = useAuthStore.getState();
  if (!refreshToken) return false;

  // Eşzamanlı 401'lerde tek bir refresh isteği yap.
  refreshPromise ??= (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        logout();
        return false;
      }
      const tokens = (await res.json()) as TokenPair;
      setTokens(tokens);
      return true;
    } catch {
      logout();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, auth = true, headers, _retry, ...rest } = options;

  const finalHeaders = new Headers(headers);
  if (body !== undefined) finalHeaders.set("Content-Type", "application/json");

  if (auth) {
    const token = useAuthStore.getState().accessToken;
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && !_retry) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return apiFetch<T>(path, { ...options, _retry: true });
    }
  }

  if (!res.ok) throw await parseError(res);

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
