import { useAuthStore } from "@shared/store/authStore";
import { ApiError } from "@shared/api/client";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

/** Bilgisayardan görsel yükler, sunucudaki kalıcı URL'i döner. */
export async function uploadImage(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);

  const token = useAuthStore.getState().accessToken;
  const res = await fetch(`${API_BASE}/uploads/image`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  });

  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      detail = (await res.json()).detail;
    } catch {
      /* gövde yok */
    }
    const message = typeof detail === "string" ? detail : "Görsel yüklenemedi";
    throw new ApiError(res.status, detail, message);
  }

  const data = (await res.json()) as { url: string };
  return data.url;
}
