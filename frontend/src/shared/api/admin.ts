import { ApiError } from "@shared/api/client";
import { useAdminStore } from "@shared/store/adminStore";
import type {
  AdminAuthResponse,
  AdminRestaurant,
  AdminTokenPair,
  FeatureCatalogItem,
  PlatformAdmin,
} from "@shared/types";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

interface AdminRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean; // varsayılan true: admin access token ekle
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
  const { refreshToken, setTokens, logout } = useAdminStore.getState();
  if (!refreshToken) return false;

  refreshPromise ??= (async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        logout();
        return false;
      }
      const tokens = (await res.json()) as AdminTokenPair;
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

async function adminFetch<T>(
  path: string,
  options: AdminRequestOptions = {},
): Promise<T> {
  const { body, auth = true, headers, _retry, ...rest } = options;

  const finalHeaders = new Headers(headers);
  if (body !== undefined) finalHeaders.set("Content-Type", "application/json");

  if (auth) {
    const token = useAdminStore.getState().accessToken;
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
      return adminFetch<T>(path, { ...options, _retry: true });
    }
  }

  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const adminApi = {
  login: (email: string, password: string) =>
    adminFetch<AdminAuthResponse>("/admin/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),

  me: () => adminFetch<PlatformAdmin>("/admin/me"),

  features: () => adminFetch<FeatureCatalogItem[]>("/admin/features"),

  restaurants: () => adminFetch<AdminRestaurant[]>("/admin/restaurants"),

  // null değer override'ı kaldırır (plan/varsayılana döner).
  updateFeatures: (restaurantId: string, features: Record<string, boolean | null>) =>
    adminFetch<AdminRestaurant>(`/admin/restaurants/${restaurantId}/features`, {
      method: "PATCH",
      body: { features },
    }),

  updatePlan: (restaurantId: string, plan: string) =>
    adminFetch<AdminRestaurant>(`/admin/restaurants/${restaurantId}/plan`, {
      method: "PATCH",
      body: { plan },
    }),
};
