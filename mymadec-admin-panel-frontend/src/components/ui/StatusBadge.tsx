import { orderStatusLabel } from "../../lib/labels";

const STATUS_CLASSES: Record<string, string> = {
  pending: "status-badge status-badge--pending",
  validated: "status-badge status-badge--validated",
  processing: "status-badge status-badge--processing",
  ready: "status-badge status-badge--ready",
  delivered: "status-badge status-badge--delivered",
  cancelled: "status-badge status-badge--cancelled",
  active: "status-badge status-badge--active",
  inactive: "status-badge status-badge--inactive",
};

const EXTRA_LABELS: Record<string, string> = {
  active: "Actif",
  inactive: "Inactif",
};

export function StatusBadge({ status }: { status: string }) {
  const className = STATUS_CLASSES[status] ?? "status-badge status-badge--neutral";
  const label = EXTRA_LABELS[status] ?? orderStatusLabel(status);
  return <span className={className}>{label}</span>;
}
