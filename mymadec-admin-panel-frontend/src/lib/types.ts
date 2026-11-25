export type PaymentMode = "especes" | "carte" | "les_deux" | "deduction_salaire";

export interface User {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  matricule: string | null;
  /** Assabil USER_LOGIN — preferred login id */
  user_login?: string | null;
  role: "admin" | "gestionnaire" | "acheteur" | "service";
  is_active: boolean;
  payment_mode: PaymentMode;
  plafond_mensuel: number | null;
  productsalesgroup_code: string | null;
  societe: string | null;
  agence: string | null;
  ville: string | null;
  langue: string;
  synced_from_intermediate: boolean;
  created_at: string;
  updated_at: string;
}

export interface CatalogGamme {
  id: number;
  name: string;
  is_active: boolean;
  sort_order: number;
}

export interface CatalogFamille {
  id: number;
  gamme_id: number;
  gamme_name?: string | null;
  name: string;
  is_active: boolean;
  sort_order: number;
}

export interface CatalogSousFamille {
  id: number;
  famille_id: number;
  famille_name?: string | null;
  gamme_name?: string | null;
  name: string;
  is_active: boolean;
  sort_order: number;
}

export interface CatalogCategorie {
  id: number;
  name: string;
  is_active: boolean;
  sort_order: number;
  image_path?: string | null;
  updated_at?: string;
}

export interface CatalogSousCategorie {
  id: number;
  categorie_id: number;
  categorie_name?: string | null;
  name: string;
  is_active: boolean;
  sort_order: number;
}

export interface CatalogType {
  id: number;
  sous_categorie_id: number;
  sous_categorie_name?: string | null;
  categorie_name?: string | null;
  name: string;
  is_active: boolean;
  sort_order: number;
  product_count?: number;
}

export interface CatalogTypeTreeNode {
  id: number;
  name: string;
  is_active: boolean;
  sort_order: number;
  product_count: number;
}

export interface CatalogSousCategorieTreeNode {
  id: number;
  name: string;
  is_active: boolean;
  sort_order: number;
  product_count: number;
  types?: CatalogTypeTreeNode[];
}

export interface CatalogCategorieTreeNode {
  id: number;
  name: string;
  is_active: boolean;
  sort_order: number;
  image_path?: string | null;
  updated_at?: string;
  product_count: number;
  sous_categories: CatalogSousCategorieTreeNode[];
}

export interface OrgSociete {
  id: number;
  code: string;
  label: string;
  is_active: boolean;
  sort_order: number;
}

export interface OrgAgence {
  id: number;
  societe_id: number;
  societe_code?: string | null;
  societe_label?: string | null;
  code: string;
  label: string;
  is_active: boolean;
  sort_order: number;
}

export interface OrgVille {
  id: number;
  code: string;
  label: string;
  is_active: boolean;
  sort_order: number;
}

export interface Product {
  id: number;
  product_code: string;
  name: string;
  description: string | null;
  unit: string | null;
  type_produit: string | null;
  gamme: string | null;
  famille: string | null;
  sous_famille: string | null;
  categorie: string | null;
  sous_categorie: string | null;
  productsalesgroup_code: string | null;
  society_code: string | null;
  base_price: number | null;
  discount_rate: number;
  is_liquidation: boolean;
  sort_order?: number;
  final_price: number | null;
  image_path: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Mobile-app product — ERP sync fields omitted. */
export interface ProductMobile {
  id: number;
  product_code: string;
  name: string;
  description: string | null;
  unit: string | null;
  type_produit: string | null;
  categorie: string | null;
  sous_categorie: string | null;
  productsalesgroup_code: string | null;
  society_code: string | null;
  base_price: number | null;
  discount_rate: number;
  is_liquidation: boolean;
  final_price: number | null;
  image_path: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderLine {
  id: number;
  sorder_line_code: number | null;
  product_code: string;
  product_name: string;
  unit_price: number;
  quantity: number;
  discount: number;
  line_amount: number;
  bl_quantity: number | null;
}

export interface Order {
  id: number;
  sorder_code: string;
  user_id: number;
  user_email: string | null;
  user_name: string | null;
  parent_order_id: number | null;
  productsalesgroup_code: string | null;
  agence: string | null;
  sorder_status: string;
  payment_mode: string;
  amount: number;
  discount_total: number;
  fixedtax: number;
  dueamount: number;
  bl_amount: number | null;
  is_flagged: boolean;
  notes: string | null;
  pushed_at: string | null;
  lines: OrderLine[];
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  body: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export interface Banner {
  id: number;
  title: string | null;
  subtitle: string | null;
  image_path: string | null;
  link_url: string | null;
  position: number;
  is_active: boolean;
  updated_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PlafondStatus {
  plafond_mensuel: number | null;
  spent_this_month: number;
  remaining: number | null;
}

export interface OrderStatusHistory {
  id: number;
  status: string;
  changed_by_id: number | null;
  notes: string | null;
  created_at: string;
}

export interface AnnuaireEntry {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  matricule: string | null;
  role: string;
  societe: string | null;
  agence: string | null;
}

export interface UnreadCount {
  unread_count: number;
}

export interface TokenRotateResponse {
  message: string;
  token: string;
  token_id: number;
}

export type DashboardPeriod =
  | "week"
  | "last_week"
  | "month"
  | "last_month"
  | "year"
  | "custom";

export interface DashboardData {
  user: {
    id: number;
    full_name: string;
    email: string;
    role: string;
    payment_mode: string;
  };
  plafond: PlafondStatus;
  recent_orders: {
    id: number;
    sorder_code: string;
    sorder_status: string;
    dueamount: number;
    created_at: string;
    buyer_name?: string;
  }[];
  banners: Banner[];
  unread_notifications: number;
  mobile_catalog: CatalogCategorieTreeNode[];
  admin_stats?: {
    period?: DashboardPeriod;
    range_from?: string;
    range_to?: string;
    orders_this_month: number;
    revenue_this_month: number;
    orders_by_status: Record<string, number>;
    series?: { label: string; count: number; amount: number }[];
    active_products: number;
    active_users: number;
    pending_orders: number;
    uncategorized_mobile_products: number;
  };
}
