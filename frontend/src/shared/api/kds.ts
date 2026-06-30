import { apiFetch } from "@shared/api/client";
import { useAuthStore } from "@shared/store/authStore";
import type { KdsItem, KdsTicket, KitchenStatus } from "@shared/types";

export const kdsApi = {
  tickets: () => apiFetch<KdsTicket[]>("/kds/tickets"),

  setItemStatus: (itemId: string, kitchen_status: KitchenStatus) =>
    apiFetch<KdsItem>(`/kds/items/${itemId}`, {
      method: "PATCH",
      body: { kitchen_status },
    }),
};

export interface RealtimeEvent {
  type: string;
  order_id?: string;
  call_id?: string;
  table_id?: string;
  table_name?: string | null;
}

/** KDS canlı kanalına WebSocket bağlantısı açar. onEvent her olayda çağrılır. */
export function connectKdsSocket(
  onEvent: (event: RealtimeEvent) => void,
  topic: "kds" | "pos" = "kds",
): () => void {
  const token = useAuthStore.getState().accessToken;
  if (!token) return () => {};

  // Dev'de /api proxy WS'i de geçirir; aynı origin üzerinden bağlan.
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${window.location.host}/api/v1/kds/ws?token=${encodeURIComponent(
    token,
  )}&topic=${topic}`;

  let closed = false;
  let ws: WebSocket | null = null;
  let retry: number | undefined;

  const open = () => {
    if (closed) return;
    ws = new WebSocket(url);
    ws.onmessage = (e) => {
      try {
        onEvent(JSON.parse(e.data));
      } catch {
        /* yoksay */
      }
    };
    ws.onclose = () => {
      if (!closed) retry = window.setTimeout(open, 2000);
    };
    ws.onerror = () => ws?.close();
  };
  open();

  return () => {
    closed = true;
    if (retry) window.clearTimeout(retry);
    ws?.close();
  };
}
