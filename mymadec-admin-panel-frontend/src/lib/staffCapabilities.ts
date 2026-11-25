import type { AppRole } from "./roles";

/** Back-office actions — mirrors backend RBAC (admin ⊃ gestionnaire for ops). */
export type StaffAction =
  | "manage_products"
  | "assign_catalog"
  | "bulk_assign_mobile"
  | "export_uncategorized"
  | "manage_catalog"
  | "import_catalog"
  | "validate_orders"
  | "view_users"
  | "create_users"
  | "edit_users"
  | "toggle_users"
  | "sync_etl"
  | "banners"
  | "annuaire"
  | "send_notifications"
  | "payment_methods_admin";

const MATRIX: Record<StaffAction, AppRole[]> = {
  manage_products: ["admin", "gestionnaire"],
  assign_catalog: ["admin", "gestionnaire"],
  bulk_assign_mobile: ["admin", "gestionnaire"],
  export_uncategorized: ["admin", "gestionnaire"],
  manage_catalog: ["admin", "gestionnaire"],
  import_catalog: ["admin"],
  validate_orders: ["admin", "gestionnaire"],
  view_users: ["admin", "gestionnaire"],
  create_users: ["admin"],
  edit_users: ["admin"],
  toggle_users: ["admin"],
  sync_etl: ["admin"],
  banners: ["admin"],
  annuaire: ["admin"],
  send_notifications: ["admin"],
  payment_methods_admin: ["admin"],
};

export function staffCan(action: StaffAction, role?: AppRole): boolean {
  if (!role) return false;
  return MATRIX[action].includes(role);
}

export function staffPageScope(
  page: keyof typeof STAFF_PAGE_SCOPE,
  role?: AppRole,
): string | undefined {
  if (role !== "admin" && role !== "gestionnaire") return undefined;
  return STAFF_PAGE_SCOPE[page][role];
}

export const STAFF_PAGE_SCOPE: Record<
  string,
  { admin: string; gestionnaire: string }
> = {
  dashboard: {
    admin:
      "Vue complète : commandes, catalogue, utilisateurs, sync ETL et bannières.",
    gestionnaire:
      "Suivi opérationnel : commandes, catalogue produits et référentiels mobile.",
  },
  products: {
    admin:
      "Gestion complète du catalogue — sync ERP, catégories mobile, export et activation.",
    gestionnaire:
      "Gestion catalogue — produits, assignation sync/mobile, sans administration système.",
  },
  catalog: {
    admin:
      "Référentiels sync + mobile + organisation. Import global réservé à l'admin.",
    gestionnaire:
      "Ajout et activation des gammes, catégories mobile, sociétés et agences.",
  },
  catalogSort: {
    admin:
      "Définir l'ordre d'affichage des catégories, sous-catégories, types et produits.",
    gestionnaire:
      "Trier le catalogue mobile : catégories, sous-catégories, types et produits.",
  },
  orders: {
    admin:
      "Suivi des commandes : En attente = pas encore prises par l'ETL ; En traitement = chez l'ERP. Statuts suivants (prête, livrée…) mis à jour via l'ETL.",
    gestionnaire:
      "Suivi des commandes (hors annulées) : En attente jusqu'à prise ETL, puis En traitement / prête / livrée selon l'ERP.",
  },
  users: {
    admin: "Création, modification, rôles, plafonds et réinitialisation MDP.",
    gestionnaire: "Consultation des fiches utilisateurs et historique commandes.",
  },
};

/** Pages réservées à l'administrateur (route guard côté App). */
export const ADMIN_PAGE_SCOPE = {
  sync: "Supervision ETL, logs de sync et rotation du token de service.",
  banners: "Contenu d'accueil de l'application mobile — images et liens.",
  annuaire: "Répertoire interne MADEC — consultation et recherche.",
  notifications: "Envoi de notifications in-app et push aux utilisateurs.",
  payment: "Attribution des modes de paiement (espèces, carte, les deux, déduction salaire) aux acheteurs.",
} as const;
