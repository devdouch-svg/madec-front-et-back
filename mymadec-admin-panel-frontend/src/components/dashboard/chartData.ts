/* Minia chart palette + client-side series helpers (no API changes:
   everything is derived from the existing /dashboard payload). */

export const MINIA_PRIMARY = "#5156be";
export const MINIA_SUCCESS = "#2ab57d";
export const MINIA_SOFT = "#777aca";
export const MINIA_MUTED = "#a8aada";

/** Order-status palette (Minia soft colors, aligned with .status-badge--*) */
export const STATUS_CHART_COLORS: Record<string, string> = {
  pending: "#ffbf53",
  validated: "#5156be",
  processing: "#777aca",
  ready: "#4ba6ef",
  delivered: "#2ab57d",
  cancelled: "#fd625e",
};

const DAY_SHORT = ["dim.", "lun.", "mar.", "mer.", "jeu.", "ven.", "sam."];

/** Axis labels for the trailing `days` window (oldest → newest). */
export function dayLabels(days = 14): string[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const labels: string[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    labels.push(`${DAY_SHORT[d.getDay()]} ${d.getDate()}`);
  }
  return labels;
}

/** Per-day order counts over the trailing `days` window (from recent_orders). */
export function dailyCounts(dates: string[], days = 14): number[] {
  return dailyBuckets(dates.map((d) => [d, 1]), days);
}

/** Per-day sum (e.g. amounts) over the trailing `days` window. */
export function dailySums(rows: [date: string, value: number][], days = 14): number[] {
  return dailyBuckets(rows, days);
}

function dailyBuckets(rows: [string, number][], days: number): number[] {
  const buckets = new Array<number>(days).fill(0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dayMs = 86_400_000;
  for (const [iso, value] of rows) {
    const d = new Date(iso);
    d.setHours(0, 0, 0, 0);
    const diff = Math.round((today.getTime() - d.getTime()) / dayMs);
    if (diff >= 0 && diff < days) buckets[days - 1 - diff] += value;
  }
  return buckets;
}
