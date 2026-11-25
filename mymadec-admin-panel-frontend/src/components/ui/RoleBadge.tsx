import { ROLE_LABELS, type AppRole } from "../../lib/roles";

const STYLES: Record<AppRole, string> = {
  admin: "bg-madec-primary-tint text-madec-primary ring-madec-border",
  gestionnaire: "bg-madec-active text-madec-primary ring-madec-border",
  acheteur: "bg-madec-successTint text-madec-success ring-madec-border",
  service: "badge-neutral ring-madec-border",
};

export function RoleBadge({ role, className = "" }: { role: AppRole; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${STYLES[role]} ${className}`}
    >
      {ROLE_LABELS[role]}
    </span>
  );
}
