import { Link, useLocation } from "react-router-dom";
import { LogOut, X } from "lucide-react";
import { Logo } from "../brand/Logo";
import { useAuth } from "../../store/auth";
import { useCart } from "../../store/cart";
import { ROLE_LABELS } from "../../lib/roles";
import { navSectionsForRole, SECTION_LABELS } from "../../lib/nav";
import { useRole } from "../../lib/roles";
import { useSidebar } from "./SidebarContext";
import { useUnreadCount } from "../../hooks/useUnreadCount";

function NavLinks({ onNavigate, unread }: { onNavigate?: () => void; unread: number }) {
  const { user } = useAuth();
  const { count } = useCart();
  const { pathname } = useLocation();
  const { isStaff, isAcheteur } = useRole();
  const groups = navSectionsForRole(user?.role);

  return (
    <>
      {groups.map(({ section, items }) => (
        <div key={section} className={section !== "main" ? "mt-2" : ""}>
          {isStaff && SECTION_LABELS[section] && (
            <p className="sidebar-section-title">{SECTION_LABELS[section]}</p>
          )}
          {items.map((item) => {
            const active = pathname.startsWith(item.to);
            const isCart = item.to === "/orders" && isAcheteur;
            const badge = item.to === "/notifications" ? unread : isCart ? count() : 0;
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                className={`sidebar-link ${active ? "sidebar-link--active" : ""}`}
              >
                <span className="sidebar-link-icon">{item.icon}</span>
                <span className="flex-1">{item.label}</span>
                {badge > 0 && (
                  <span className="rounded-full bg-madec-danger px-1.5 py-0.5 text-xs font-medium text-white">
                    {badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      ))}
    </>
  );
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const { mobileOpen, setMobileOpen } = useSidebar();
  const { data: unreadData } = useUnreadCount();
  const unread = unreadData?.unread_count ?? 0;

  const closeMobile = () => setMobileOpen(false);

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          aria-label="Fermer le menu"
          onClick={closeMobile}
        />
      )}

      <aside
        className={`app-sidebar fixed inset-y-0 left-0 z-50 flex h-screen w-[250px] flex-col lg:static lg:z-auto lg:shrink-0 lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } transition-transform duration-200`}
      >
        <div className="flex h-[70px] shrink-0 items-center justify-between border-b border-madec-border px-5">
          <Link to="/dashboard" onClick={closeMobile} className="block py-1">
            <Logo on="light" className="sidebar-logo" />
          </Link>
          <button
            type="button"
            onClick={closeMobile}
            className="rounded p-1 text-madec-muted hover:text-madec-text lg:hidden"
            aria-label="Fermer le menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
          <NavLinks onNavigate={closeMobile} unread={unread} />
        </nav>

        <div className="border-t border-madec-border p-3">
          <Link
            to="/profile"
            onClick={closeMobile}
            className={`mb-2 block rounded px-3 py-2 transition-colors ${
              pathname === "/profile" ? "bg-madec-tint" : "hover:bg-madec-active"
            }`}
          >
            <p className="truncate text-sm font-medium text-madec-text">
              {user?.first_name ? `${user.first_name} ${user.last_name ?? ""}`.trim() : user?.email}
            </p>
            <p className="truncate text-xs text-madec-muted">
              {user?.role ? ROLE_LABELS[user.role] : ""}
            </p>
          </Link>
          <button
            type="button"
            onClick={() => { logout(); closeMobile(); }}
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-sm text-madec-secondary transition-colors hover:text-madec-danger"
          >
            <LogOut size={16} />
            Déconnexion
          </button>
        </div>
      </aside>
    </>
  );
}
