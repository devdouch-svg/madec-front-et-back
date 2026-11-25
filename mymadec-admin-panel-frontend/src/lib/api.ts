import axios from "axios";
import toast from "react-hot-toast";
import { API_BASE_URL, LOGIN_URL } from "./config";
import { getErrorMessage } from "./errors";
import { clearSession, getAccessToken, getRefreshToken } from "./session";
import { useAuth } from "../store/auth";

const BASE_URL = API_BASE_URL;

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

// ── Request: attach access token ─────────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response: silent token refresh on 401 ───────────────────────────────────
let isRefreshing = false;
let waitQueue: Array<(token: string | null) => void> = [];

function drainQueue(token: string | null) {
  waitQueue.forEach((cb) => cb(token));
  waitQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 403) {
      toast.error(getErrorMessage(error, "Accès refusé"));
      return Promise.reject(error);
    }

    if (
      error.response?.status !== 401 ||
      original._retry ||
      original.url?.includes("/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    original._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        waitQueue.push((token) => {
          if (!token) return reject(error);
          original.headers.Authorization = `Bearer ${token}`;
          resolve(api(original));
        });
      });
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearSession();
      useAuth.setState({ user: null, accessToken: null, refreshToken: null });
      window.location.replace(LOGIN_URL);
      return Promise.reject(error);
    }

    isRefreshing = true;

    try {
      const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      useAuth.getState().setTokens(data.access_token, data.refresh_token);
      drainQueue(data.access_token);

      original.headers.Authorization = `Bearer ${data.access_token}`;
      return api(original);
    } catch {
      drainQueue(null);
      clearSession();
      useAuth.setState({ user: null, accessToken: null, refreshToken: null });
      window.location.replace(LOGIN_URL);
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;
