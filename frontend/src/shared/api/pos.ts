import { apiFetch } from "@shared/api/client";
import type {
  DashboardSummary,
  Order,
  TableWithStatus,
  WaiterCall,
} from "@shared/types";

export const dashboardApi = {
  summary: () => apiFetch<DashboardSummary>("/orders/summary"),
};

export const waiterCallsApi = {
  list: () => apiFetch<WaiterCall[]>("/waiter-calls"),

  resolve: (id: string) =>
    apiFetch<WaiterCall>(`/waiter-calls/${id}/resolve`, { method: "POST" }),
};

export const tablesApi = {
  list: () => apiFetch<TableWithStatus[]>("/tables"),

  create: (name: string, sort_order = 0) =>
    apiFetch<TableWithStatus>("/tables", { method: "POST", body: { name, sort_order } }),

  bulkCreate: (count: number) =>
    apiFetch<TableWithStatus[]>(`/tables/bulk?count=${count}`, { method: "POST" }),

  update: (id: string, data: { name?: string; sort_order?: number }) =>
    apiFetch<TableWithStatus>(`/tables/${id}`, { method: "PATCH", body: data }),

  remove: (id: string) => apiFetch<void>(`/tables/${id}`, { method: "DELETE" }),
};

export const ordersApi = {
  open: (table_id: string) =>
    apiFetch<Order>("/orders/open", { method: "POST", body: { table_id } }),

  get: (id: string) => apiFetch<Order>(`/orders/${id}`),

  addItem: (
    orderId: string,
    menu_item_id: string,
    quantity = 1,
    note?: string,
    modifier_ids: string[] = [],
  ) =>
    apiFetch<Order>(`/orders/${orderId}/items`, {
      method: "POST",
      body: { menu_item_id, quantity, note, modifier_ids },
    }),

  updateItem: (orderId: string, itemId: string, quantity: number) =>
    apiFetch<Order>(`/orders/${orderId}/items/${itemId}`, {
      method: "PATCH",
      body: { quantity },
    }),

  removeItem: (orderId: string, itemId: string) =>
    apiFetch<Order>(`/orders/${orderId}/items/${itemId}`, { method: "DELETE" }),

  setDiscount: (orderId: string, mode: "percent" | "amount", value: number) =>
    apiFetch<Order>(`/orders/${orderId}/discount`, {
      method: "POST",
      body: { mode, value },
    }),

  setServiceCharge: (orderId: string, rate: number) =>
    apiFetch<Order>(`/orders/${orderId}/service-charge`, {
      method: "POST",
      body: { rate },
    }),

  applyCoupon: (orderId: string, code: string) =>
    apiFetch<Order>(`/orders/${orderId}/apply-coupon`, {
      method: "POST",
      body: { code },
    }),

  payFull: (orderId: string, method = "cash", tip_amount = 0) =>
    apiFetch<Order>(`/orders/${orderId}/pay`, {
      method: "POST",
      body: { method, tip_amount },
    }),

  payItems: (orderId: string, item_ids: string[], method = "cash", tip_amount = 0) =>
    apiFetch<Order>(`/orders/${orderId}/pay-items`, {
      method: "POST",
      body: { item_ids, method, tip_amount },
    }),

  paySplit: (orderId: string, parts: number, method = "cash", tip_amount = 0) =>
    apiFetch<Order>(`/orders/${orderId}/pay-split`, {
      method: "POST",
      body: { parts, method, tip_amount },
    }),
};
