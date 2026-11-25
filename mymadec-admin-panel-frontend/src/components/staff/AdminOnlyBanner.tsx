import { ADMIN_PAGE_SCOPE } from "../../lib/staffCapabilities";
import { RoleBadge } from "../ui/RoleBadge";

export function AdminOnlyBanner({ page }: { page: keyof typeof ADMIN_PAGE_SCOPE }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-violet-200 bg-violet-50/60 px-4 py-3 text-sm text-violet-900">
      <RoleBadge role="admin" />
      <span>{ADMIN_PAGE_SCOPE[page]}</span>
    </div>
  );
}
