import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "../lib/api";
import { clearSession } from "../lib/session";
import type { User } from "../lib/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;

  login: (matricule: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,

      setTokens: (access, refresh) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ accessToken: access, refreshToken: refresh });
      },

      login: async (matricule, password) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post("/auth/login", { matricule, password });
          get().setTokens(data.access_token, data.refresh_token);
          set({ user: null });
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        try {
          await api.post("/auth/logout");
        } catch {
          // Client clears session regardless
        }
        clearSession();
        set({ user: null, accessToken: null, refreshToken: null });
      },

      fetchMe: async () => {
        const { data } = await api.get<User>("/users/me");
        set({ user: data });
      },
    }),
    {
      name: "mymadec-auth",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        user: s.user,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          if (state.accessToken) localStorage.setItem("access_token", state.accessToken);
          if (state.refreshToken) localStorage.setItem("refresh_token", state.refreshToken);
        }
      },
    },
  ),
);
