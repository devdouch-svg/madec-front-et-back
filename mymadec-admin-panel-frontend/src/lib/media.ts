import { apiServerOrigin } from "./config";

const UPLOAD_PREFIX = "/uploads/";

/** Normalize backend paths (Docker `/app/uploads/...`, relative `uploads/...`) to `/uploads/...`. */
export function normalizeUploadPath(path: string): string {
  let normalized = path.trim().replace(/\\/g, "/");

  // Absolute URL already pointing at /uploads — keep path only
  if (/^https?:\/\//i.test(normalized)) {
    try {
      const u = new URL(normalized);
      normalized = u.pathname;
    } catch {
      return "";
    }
  }

  // Docker absolute path stored in DB: /app/uploads/banners/x.png
  if (normalized.startsWith("/app/uploads/")) {
    normalized = normalized.slice("/app".length);
  }

  // Sometimes stored as "uploads/..." or nested ".../uploads/..."
  const idx = normalized.toLowerCase().indexOf("/uploads/");
  if (idx >= 0) {
    normalized = normalized.slice(idx);
  } else if (normalized.toLowerCase().startsWith("uploads/")) {
    normalized = `/${normalized}`;
  }

  if (!normalized.startsWith("/")) {
    normalized = `/${normalized}`;
  }

  if (!normalized.startsWith(UPLOAD_PREFIX)) {
    return "";
  }

  return normalized;
}

/** Build URL for uploaded images (products, banners). Rejects arbitrary external URLs. */
export function mediaUrl(
  path: string | null | undefined,
  cacheKey?: string | number | null,
): string {
  if (!path) return "";

  const normalized = normalizeUploadPath(path);
  if (!normalized) return "";

  const origin = apiServerOrigin();
  const base = origin ? `${origin}${normalized}` : normalized;

  if (cacheKey == null || cacheKey === "") return base;
  return `${base}?v=${encodeURIComponent(String(cacheKey))}`;
}
