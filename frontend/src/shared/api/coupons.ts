import { apiFetch } from "@shared/api/client";

export interface Coupon {
  id: string;
  restaurant_id: string;
  code: string;
  mode: "percent" | "amount";
  value: string;
  is_active: boolean;
  created_at: string;
}

export const couponsApi = {
  list: () => apiFetch<Coupon[]>("/coupons"),

  create: (code: string, mode: "percent" | "amount", value: number) =>
    apiFetch<Coupon>("/coupons", {
      method: "POST",
      body: { code, mode, value },
    }),

  remove: (id: string) => apiFetch<void>(`/coupons/${id}`, { method: "DELETE" }),
};
