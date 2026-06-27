import { apiFetch } from "@shared/api/client";
import type {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  Restaurant,
  User,
} from "@shared/types";

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: payload,
      auth: false,
    }),

  login: (payload: LoginPayload) =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: payload,
      auth: false,
    }),

  me: () => apiFetch<User>("/auth/me"),

  myRestaurant: () => apiFetch<Restaurant>("/auth/me/restaurant"),
};
