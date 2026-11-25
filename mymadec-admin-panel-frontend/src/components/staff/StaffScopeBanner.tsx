import { STAFF_PAGE_SCOPE } from "../../lib/staffCapabilities";
import type { AppRole } from "../../lib/roles";
import { RoleBadge } from "../ui/RoleBadge";

export function StaffScopeBanner({
  page,
  role,
}: {
  page: keyof typeof STAFF_PAGE_SCOPE;
  role: AppRole;
}) {
  if (role !== "admin" && role !== "gestionnaire") return null;
  const scope = STAFF_PAGE_SCOPE[page][role];
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-madec-border bg-madec-surface/80 px-4 py-3 text-sm text-madec-secondary">
      <RoleBadge role={role} />
      <span>{scope}</span>
    </div>
  );
}
