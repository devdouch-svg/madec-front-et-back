import type { ReactNode } from "react";
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Users,
  BookUser,
  Bell,
  CreditCard,
  Image,
  RefreshCw,
  Layers,
  Sparkles,
  ArrowUpDown,
} from "lucide-react";
import { createElement } from "react";
import type { AppRole } from "./roles";

export type NavSection = "main" | "operations" | "administration";

export interface NavItem {
  to: string;
  icon: ReactNode;
  label: string;
  roles?: AppRole[];
  section?: NavSection;
}

const SECTION_LABELS: Record<NavSection, string> = {
  main: "",
  operations: "Gestion",
  administration: "Administration",
};

const icon = (c: typeof LayoutDashboard) => createElement(c, { size: 18 });

const ALL: NavItem[] = [
  { to: "/dashboard", icon: icon(LayoutDashboard), label: "Tableau de bord", section: "main" },
  { to: "/products", icon: icon(Package), label: "Produits", section: "main" },
  { to: "/promptinos", icon: icon(Sparkles), label: "Promptinos", section: "main" },
  { to: "/orders", icon: icon(ShoppingCart), label: "Commandes", section: "main" },
  { to: "/notifications", icon: icon(Bell), label: "Notifications", section: "main" },
  { to: "/users", icon: icon(Users), label: "Utilisateurs", roles: ["admin", "gestionnaire"], section: "operations" },
  { to: "/catalog", icon: icon(Layers), label: "Référentiels", roles: ["admin", "gestionnaire"], section: "operations" },
  { to: "/catalog/order", icon: icon(ArrowUpDown), label: "Ordre catalogue", roles: ["admin", "gestionnaire"], section: "operations" },
  { to: "/annuaire", icon: icon(BookUser), label: "Annuaire", roles: ["admin"], section: "administration" },
  { to: "/banners", icon: icon(Image), label: "Bannières", roles: ["admin"], section: "administration" },
  { to: "/sync", icon: icon(RefreshCw), label: "Sync ETL", roles: ["admin"], section: "administration" },
  // Admin only — acheteurs see their mode on profile / checkout, not a dedicated always-visible screen
  { to: "/payment-methods", icon: icon(CreditCard), label: "Paiement", roles: ["admin"], section: "administration" },
];

export function navSectionsForRole(role?: AppRole): { section: NavSection; items: NavItem[] }[] {
  const items = navForRole(role);
  const order: NavSection[] = ["main", "operations", "administration"];
  return order
    .map((section) => ({
      section,
      items: items.filter((i) => (i.section ?? "main") === section),
    }))
    .filter((g) => g.items.length > 0);
}

export { SECTION_LABELS };

export function navForRole(role?: AppRole): NavItem[] {
  return ALL.filter((item) => !item.roles || (role && item.roles.includes(role)))
    .map((item) => {
      if (role === "acheteur" && item.to === "/products") {
        return { ...item, label: "Catalogue" };
      }
      if (role === "acheteur" && item.to === "/orders") {
        return { ...item, label: "Mes commandes" };
      }
      if (role === "acheteur" && item.to === "/promptinos") {
        return { ...item, label: "Sélection Promptinos" };
      }
      return item;
    });
}
