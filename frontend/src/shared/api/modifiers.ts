import { apiFetch } from "@shared/api/client";

export interface Modifier {
  id: string;
  modifier_group_id: string;
  name: string;
  price_delta: string;
  is_available: boolean;
  sort_order: number;
}

export interface ModifierGroup {
  id: string;
  restaurant_id: string;
  name: string;
  selection_type: "single" | "multiple";
  min_select: number;
  max_select: number;
  is_required: boolean;
  sort_order: number;
  is_active: boolean;
  modifiers: Modifier[];
}

export interface NewModifier {
  name: string;
  price_delta: number;
}

export interface NewGroup {
  name: string;
  selection_type: "single" | "multiple";
  min_select: number;
  max_select: number;
  is_required: boolean;
  modifiers: NewModifier[];
}

export const modifiersApi = {
  listGroups: () => apiFetch<ModifierGroup[]>("/modifier-groups"),

  createGroup: (data: NewGroup) =>
    apiFetch<ModifierGroup>("/modifier-groups", { method: "POST", body: data }),

  deleteGroup: (id: string) =>
    apiFetch<void>(`/modifier-groups/${id}`, { method: "DELETE" }),

  updateGroup: (
    id: string,
    data: Partial<{
      name: string;
      selection_type: "single" | "multiple";
      is_required: boolean;
      min_select: number;
      max_select: number;
    }>,
  ) => apiFetch<ModifierGroup>(`/modifier-groups/${id}`, { method: "PATCH", body: data }),

  addModifier: (groupId: string, data: NewModifier) =>
    apiFetch<ModifierGroup>(`/modifier-groups/${groupId}/modifiers`, {
      method: "POST",
      body: data,
    }),

  updateModifier: (id: string, data: { name?: string; price_delta?: number }) =>
    apiFetch<ModifierGroup>(`/modifiers/${id}`, { method: "PATCH", body: data }),

  deleteModifier: (id: string) =>
    apiFetch<void>(`/modifiers/${id}`, { method: "DELETE" }),

  itemGroups: (itemId: string) =>
    apiFetch<ModifierGroup[]>(`/menu-items/${itemId}/modifier-groups`),

  assignGroups: (itemId: string, group_ids: string[]) =>
    apiFetch<ModifierGroup[]>(`/menu-items/${itemId}/modifier-groups`, {
      method: "PUT",
      body: { group_ids },
    }),
};
