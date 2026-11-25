/** Axios base path for REST calls (relative in prod behind nginx). */
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

/** App base path ("/") — v2 is the main app at the root. */
export const APP_BASE_URL = import.meta.env.BASE_URL;

/** Login page URL for hard (non-router) redirects. */
export const LOGIN_URL = `${APP_BASE_URL}login`;

/**
 * Origin used for /uploads media URLs.
 * Never use VITE_DEV_PROXY_TARGET here — that is server-only (Vite proxy) and is often
 * 127.0.0.1, which breaks images when the UI is opened from another machine/LAN IP.
 * Prefer relative /uploads (same host as the page) so Vite/nginx can proxy.
 */
export function apiServerOrigin(): string {
  const explicit = import.meta.env.VITE_MEDIA_BASE_URL?.trim();
  if (explicit) return explicit.replace(/\/$/, "");

  const apiBase = import.meta.env.VITE_API_URL ?? "/api/v1";
  try {
    if (apiBase.startsWith("http://") || apiBase.startsWith("https://")) {
      return new URL(apiBase).origin;
    }
  } catch {
    // fall through
  }

  // Relative API (/api/v1) → relative media (/uploads/...) via current page origin.
  // Empty string keeps paths relative; window.origin also works when absolute is needed.
  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  return "";
}
