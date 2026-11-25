/** French UI labels for API enum values, and shared formatting helpers */

export const ORDER_STATUS_LABELS: Record<string, string> = {
  pending:    "En attente",
  // Same meaning as pending for the ETL queue (no admin validation step)
  validated:  "En attente",
  processing: "Traitement en cours",
  ready:      "Commande prête à récupérer",
  delivered:  "Commande récupérée",
  cancelled:  "Commande annulée",
};

export const PAYMENT_MODE_LABELS: Record<string, string> = {
  carte:              "Carte",
  especes:            "Espèces",
  les_deux:           "Espèces & Carte",
  deduction_salaire:  "Déduction salaire",
};

export const ATOMIC_PAYMENT_MODES = ["especes", "carte", "deduction_salaire"] as const;

/** Alias — used by UsersPage and PaymentMethodsPage */
export const PAYMENT_LABELS = PAYMENT_MODE_LABELS;

export function orderStatusLabel(status: string): string {
  return ORDER_STATUS_LABELS[status] ?? status;
}

/** Expand stored payment_mode (legacy les_deux or comma-list) to atomic modes. */
export function expandPaymentModes(raw: string | null | undefined): string[] {
  if (!raw) return ["especes"];
  if (raw === "les_deux") return ["especes", "carte"];
  if (raw.includes(",")) {
    const set = new Set(raw.split(",").map((s) => s.trim()).filter(Boolean));
    return ATOMIC_PAYMENT_MODES.filter((m) => set.has(m));
  }
  if ((ATOMIC_PAYMENT_MODES as readonly string[]).includes(raw)) return [raw];
  return [raw];
}

export function paymentModeLabel(mode: string): string {
  return expandPaymentModes(mode)
    .map((m) => PAYMENT_MODE_LABELS[m] ?? m)
    .join(" + ");
}

/** Format a number as a MAD amount: "1 234.50 MAD" */
export function formatMAD(amount: number): string {
  return `${amount.toLocaleString("fr-MA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} MAD`;
}
