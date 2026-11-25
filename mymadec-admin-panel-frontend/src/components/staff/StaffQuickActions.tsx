import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  Clock,
  Package,
  Layers,
  Users,
  RefreshCw,
  Image,
  BookUser,
  Smartphone,
  ShoppingCart,
  Sparkles,
} from "lucide-react";
import type { DashboardData } from "../../lib/types";

interface ActionCard {
  to: string;
  label: string;
  description: string;
  icon: ReactNode;
  highlight?: boolean;
}

function ActionGrid({ items }: { items: ActionCard[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          className={`card group flex items-start gap-3 transition-shadow hover:shadow-card-hover ${
            item.highlight ? "ring-1 ring-amber-200 bg-amber-50/40" : ""
          }`}
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-madec-active text-madec-primary group-hover:bg-madec-tint">
            {item.icon}
          </div>
          <div>
            <p className="text-sm font-semibold text-madec-text">{item.label}</p>
            <p className="text-xs text-madec-muted">{item.description}</p>
          </div>
        </Link>
      ))}
    </div>
  );
}

export function StaffQuickActions({
  isAdmin,
  stats,
}: {
  isAdmin: boolean;
  stats?: DashboardData["admin_stats"];
}) {
  const pending = stats?.pending_orders ?? 0;
  const uncategorized = stats?.uncategorized_mobile_products ?? 0;

  const shared: ActionCard[] = [
    {
      to: "/orders?status=pending",
      label: "Commandes en attente",
      description: pending > 0 ? `${pending} avant prise ETL` : "Aucune en attente",
      icon: <Clock size={18} />,
      highlight: pending > 0,
    },
    {
      to: "/products",
      label: "Catalogue produits",
      description: "Créer, modifier, assigner",
      icon: <Package size={18} />,
    },
    {
      to: "/promptinos",
      label: "Promptinos",
      description: "Vue gamme dédiée",
      icon: <Sparkles size={18} />,
    },
    {
      to: "/catalog",
      label: "Référentiels",
      description: "Sync ERP + catégories mobile",
      icon: <Layers size={18} />,
    },
  ];

  if (uncategorized > 0) {
    shared.push({
      to: "/products?missing_mobile_category=true",
      label: "Sans catégorie mobile",
      description: `${uncategorized} produit(s) à classer`,
      icon: <Smartphone size={18} />,
      highlight: true,
    });
  }

  const gestOnly: ActionCard[] = [
    ...shared,
    {
      to: "/users",
      label: "Utilisateurs",
      description: "Consultation en lecture seule",
      icon: <Users size={18} />,
    },
    {
      to: "/orders",
      label: "Toutes les commandes",
      description: "Filtres et changements de statut",
      icon: <ShoppingCart size={18} />,
    },
  ];

  const adminOnly: ActionCard[] = [
    ...shared,
    {
      to: "/users",
      label: "Utilisateurs",
      description: "Création, rôles, plafonds",
      icon: <Users size={18} />,
    },
    {
      to: "/sync",
      label: "Sync ETL",
      description: "Serveur intermédiaire",
      icon: <RefreshCw size={18} />,
    },
    {
      to: "/banners",
      label: "Bannières",
      description: "Accueil application mobile",
      icon: <Image size={18} />,
    },
    {
      to: "/annuaire",
      label: "Annuaire",
      description: "Contacts MADEC",
      icon: <BookUser size={18} />,
    },
  ];

  return (
    <div className="space-y-3">
      <h2 className="section-title">
        {isAdmin ? "Administration" : "Actions rapides"}
      </h2>
      <ActionGrid items={isAdmin ? adminOnly : gestOnly} />
    </div>
  );
}
