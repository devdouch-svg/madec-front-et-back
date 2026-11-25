import { useEffect, useRef, useState } from "react";
import {
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  Search,
  Settings,
  UserRound,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../store/auth";
import { useSidebar } from "./SidebarContext";
import { useUnreadCount } from "../../hooks/useUnreadCount";
import type { User } from "../../lib/types";

function userInitials(user: User | null): string {
  if (!user) return "?";
  if (user.first_name) {
    const first = user.first_name[0] ?? "";
    const last = user.last_name?.[0] ?? "";
    const initials = `${first}${last}`.trim();
    if (initials) return initials.toUpperCase();
  }
  return (user.email?.[0] ?? "?").toUpperCase();
}

function shortDisplayName(user: User | null): string {
  if (!user) return "";
  if (user.first_name) {
    const last = user.last_name?.[0] ? ` ${user.last_name[0]}.` : "";
    return `${user.first_name}${last}`;
  }
  return user.email?.split("@")[0] ?? "";
}

export function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { toggleMobile } = useSidebar();
  const { data } = useUnreadCount();
  const unread = data?.unread_count ?? 0;

  const [query, setQuery] = useState("");
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!userMenuOpen) return;
    const onDoc = (e: MouseEvent) => {
      if (!userMenuRef.current?.contains(e.target as Node)) setUserMenuOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [userMenuOpen]);

  const submitSearch = (e?: React.FormEvent) => {
    e?.preventDefault();
    const q = query.trim();
    if (q.length < 2) return;
    navigate(`/products?search=${encodeURIComponent(q)}`);
    setMobileSearchOpen(false);
  };

  return (
    <header className="app-topbar">
      <div className="navbar-header">
        {/* ── Left: menu + search (Minia) ─────────────────────────────── */}
        <div className="navbar-header-start">
          <button
            type="button"
            onClick={toggleMobile}
            className="header-item header-item--menu lg:hidden"
            aria-label="Ouvrir le menu"
            id="vertical-menu-btn"
          >
            <Menu size={18} strokeWidth={2} />
          </button>

          <form className="app-search hidden lg:block" onSubmit={submitSearch}>
            <div className="app-search-inner">
              <input
                type="search"
                className="app-search-input"
                placeholder="Rechercher…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Rechercher un produit"
              />
              <button type="submit" className="app-search-btn" aria-label="Lancer la recherche">
                <Search size={16} strokeWidth={2.25} />
              </button>
            </div>
          </form>
        </div>

        {/* ── Right: header items (Minia) ─────────────────────────────── */}
        <div className="navbar-header-end">
          <button
            type="button"
            className="header-item lg:hidden"
            aria-label="Rechercher"
            onClick={() => setMobileSearchOpen((o) => !o)}
          >
            <Search size={20} strokeWidth={1.75} />
          </button>

          <Link
            to="/notifications"
            className="header-item noti-icon"
            title="Notifications"
            aria-label={`Notifications${unread > 0 ? ` (${unread})` : ""}`}
          >
            <Bell size={20} strokeWidth={1.75} />
            {unread > 0 && (
              <span className="noti-badge">{unread > 9 ? "9+" : unread}</span>
            )}
          </Link>

          <Link
            to="/profile"
            className="header-item hidden sm:inline-flex"
            title="Paramètres"
            aria-label="Paramètres du profil"
          >
            <Settings size={20} strokeWidth={1.75} />
          </Link>

          <div className="relative" ref={userMenuRef}>
            <button
              type="button"
              className="header-item header-item--user"
              aria-haspopup="menu"
              aria-expanded={userMenuOpen}
              onClick={() => setUserMenuOpen((o) => !o)}
            >
              <span
                className={`header-profile-user${user?.role === "gestionnaire" ? " header-profile-user--gestionnaire" : ""}`}
                aria-hidden
              >
                {userInitials(user)}
              </span>
              <span className="header-user-name hidden xl:inline">{shortDisplayName(user)}</span>
              <ChevronDown size={16} className="hidden xl:inline text-madec-muted" />
            </button>

            {userMenuOpen && (
              <div className="topbar-dropdown" role="menu">
                <Link
                  to="/profile"
                  role="menuitem"
                  className="topbar-dropdown-item"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <UserRound size={16} />
                  Profil
                </Link>
                <div className="topbar-dropdown-divider" />
                <button
                  type="button"
                  role="menuitem"
                  className="topbar-dropdown-item topbar-dropdown-item--danger"
                  onClick={() => {
                    setUserMenuOpen(false);
                    void logout();
                  }}
                >
                  <LogOut size={16} />
                  Déconnexion
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile search dropdown */}
      {mobileSearchOpen && (
        <form className="app-search-mobile lg:hidden" onSubmit={submitSearch}>
          <input
            type="search"
            className="app-search-input"
            placeholder="Rechercher…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            aria-label="Rechercher un produit"
          />
          <button type="submit" className="app-search-btn" aria-label="Lancer la recherche">
            <Search size={16} />
          </button>
        </form>
      )}
    </header>
  );
}
