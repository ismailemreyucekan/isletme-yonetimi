import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AdminAuthResponse, AdminTokenPair, PlatformAdmin } from "@shared/types";

interface AdminAuthState {
  accessToken: string | null;
  refreshToken: string | null;
  admin: PlatformAdmin | null;
  setAuth: (auth: AdminAuthResponse) => void;
  setTokens: (tokens: AdminTokenPair) => void;
  logout: () => void;
}

// Personel (kasa-auth) deposundan ayrı tutulur; aynı tarayıcıda hem personel
// hem yönetici oturumu çakışmadan açılabilsin.
export const useAdminStore = create<AdminAuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      admin: null,
      setAuth: (auth) =>
        set({
          accessToken: auth.access_token,
          refreshToken: auth.refresh_token,
          admin: auth.admin,
        }),
      setTokens: (tokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        }),
      logout: () => set({ accessToken: null, refreshToken: null, admin: null }),
    }),
    { name: "kasa-admin-auth" },
  ),
);
