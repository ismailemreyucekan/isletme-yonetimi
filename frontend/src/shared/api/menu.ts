import { apiFetch } from "@shared/api/client";
import type {
  MenuCategory,
  MenuCategoryCreate,
  MenuItem,
  MenuItemCreate,
} from "@shared/types";

export const menuApi = {
  // Kategoriler
  listCategories: () => apiFetch<MenuCategory[]>("/menu/categories"),

  createCategory: (data: MenuCategoryCreate) =>
    apiFetch<MenuCategory>("/menu/categories", { method: "POST", body: data }),

  updateCategory: (id: string, data: Partial<MenuCategoryCreate>) =>
    apiFetch<MenuCategory>(`/menu/categories/${id}`, { method: "PATCH", body: data }),

  deleteCategory: (id: string) =>
    apiFetch<void>(`/menu/categories/${id}`, { method: "DELETE" }),

  // Ürünler
  listItems: () => apiFetch<MenuItem[]>("/menu/items"),

  createItem: (data: MenuItemCreate) =>
    apiFetch<MenuItem>("/menu/items", { method: "POST", body: data }),

  updateItem: (id: string, data: Partial<MenuItemCreate> & { is_available?: boolean }) =>
    apiFetch<MenuItem>(`/menu/items/${id}`, { method: "PATCH", body: data }),

  deleteItem: (id: string) =>
    apiFetch<void>(`/menu/items/${id}`, { method: "DELETE" }),
};
