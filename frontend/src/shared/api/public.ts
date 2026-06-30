import { apiFetch } from "@shared/api/client";
import type { ModifierGroup } from "@shared/api/modifiers";
import type { MenuCategory, MenuItem, Order } from "@shared/types";

export interface PublicRestaurant {
  name: string;
  slug: string;
  currency: string;
}

export interface PublicTableView {
  restaurant: PublicRestaurant;
  table_name: string;
  order: Order | null;
}

export interface PublicMenuView {
  restaurant: PublicRestaurant;
  categories: MenuCategory[];
  items: MenuItem[];
}

export interface PublicTableListItem {
  name: string;
  qr_token: string;
  status: "empty" | "occupied";
}

export interface PublicTableList {
  restaurant: PublicRestaurant;
  tables: PublicTableListItem[];
}

// Müşteri tarafı: auth YOK, masa qr_token ile yetkilenir.
export const publicApi = {
  tableView: (token: string) =>
    apiFetch<PublicTableView>(`/public/t/${token}`, { auth: false }),

  menu: (token: string) =>
    apiFetch<PublicMenuView>(`/public/t/${token}/menu`, { auth: false }),

  menuBySlug: (slug: string) =>
    apiFetch<PublicMenuView>(`/public/r/${slug}/menu`, { auth: false }),

  tablesBySlug: (slug: string) =>
    apiFetch<PublicTableList>(`/public/r/${slug}/tables`, { auth: false }),

  itemOptions: (token: string, itemId: string) =>
    apiFetch<ModifierGroup[]>(`/public/t/${token}/menu-item/${itemId}/options`, {
      auth: false,
    }),

  placeOrder: (
    token: string,
    items: { menu_item_id: string; quantity: number; modifier_ids?: string[] }[],
  ) =>
    apiFetch<Order>(`/public/t/${token}/order`, {
      method: "POST",
      auth: false,
      body: { items },
    }),

  payFull: (token: string) =>
    apiFetch<Order>(`/public/t/${token}/pay`, { method: "POST", auth: false }),

  payItems: (token: string, item_ids: string[]) =>
    apiFetch<Order>(`/public/t/${token}/pay-items`, {
      method: "POST",
      auth: false,
      body: { item_ids },
    }),

  paySplit: (token: string, parts: number) =>
    apiFetch<Order>(`/public/t/${token}/pay-split`, {
      method: "POST",
      auth: false,
      body: { parts },
    }),

  callWaiter: (token: string, note?: string) =>
    apiFetch<{ status: string; message: string }>(`/public/t/${token}/call-waiter`, {
      method: "POST",
      auth: false,
      body: { note: note ?? null },
    }),
};
