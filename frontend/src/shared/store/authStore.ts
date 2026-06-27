import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthResponse, TokenPair, User } from "@shared/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setAuth: (auth: AuthResponse) => void;
  setTokens: (tokens: TokenPair) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setAuth: (auth) =>
        set({
          accessToken: auth.access_token,
          refreshToken: auth.refresh_token,
          user: auth.user,
        }),
      setTokens: (tokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "kasa-auth" },
  ),
);

export const isAuthenticated = () => Boolean(useAuthStore.getState().accessToken);
