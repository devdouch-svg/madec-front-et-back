interface ValidationFieldError {
  field?: string;
  message?: string;
}

/**
 * Extract a human-readable message from an Axios error.
 *
 * Backend always returns {"detail": string | object}.
 * Validation errors also include {"fields": [{field, message}, ...]}.
 * PlafondExceededException returns {"detail": {code, message, available, requested}}.
 */
export function getErrorMessage(e: unknown, fallback = "Une erreur est survenue"): string {
  const data = (e as any)?.response?.data;
  const detail = data?.detail;
  const fields = data?.fields as ValidationFieldError[] | undefined;

  if (Array.isArray(fields) && fields.length > 0) {
    const messages = fields
      .map((f) => cleanValidationMessage(f.message))
      .filter((msg): msg is string => Boolean(msg));
    if (messages.length > 0) return messages.join(" ");
  }

  if (!detail) return fallback;
  if (typeof detail === "string") {
    return detail === "Validation error" ? fallback : detail;
  }
  if (typeof detail === "object" && typeof detail.message === "string") return detail.message;
  return fallback;
}

function cleanValidationMessage(message?: string): string | undefined {
  if (!message) return undefined;
  return message.replace(/^Value error,\s*/i, "").trim();
}

/**
 * Plafond-exceeded typed payload returned by the backend.
 */
export interface PlafondError {
  code: "PLAFOND_EXCEEDED";
  message: string;
  available: number;
  requested: number;
}

export function isPlafondError(e: unknown): e is { response: { data: { detail: PlafondError } } } {
  return (e as any)?.response?.data?.detail?.code === "PLAFOND_EXCEEDED";
}
