/**
 * Typed API client — maps 1:1 to backend /api/v1 routes.
 * ETL machine endpoints (/sync/products, etc.) use a service token and are not called from the web UI.
 */
import api from "../api";
import type {
  AnnuaireEntry,
  Banner,
  CatalogFamille,
  CatalogGamme,
  CatalogCategorie,
  CatalogCategorieTreeNode,
  CatalogSousCategorie,
  CatalogSousFamille,
  CatalogType,
  DashboardData,
  Notification,
  Order,
  OrderLine,
  OrderStatusHistory,
  OrgAgence,
  OrgSociete,
  OrgVille,
  PaginatedResponse,
  PlafondStatus,
  Product,
  ProductMobile,
  TokenRotateResponse,
  User,
} from "../types";

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  logout: () => api.post("/auth/logout"),
  refresh: (refresh_token: string) => api.post("/auth/refresh", { refresh_token }),
  requestPasswordReset: (email: string) =>
    api.post("/auth/reset-password/request", { email }),
  confirmPasswordReset: (token: string, new_password: string) =>
    api.post("/auth/reset-password/confirm", { token, new_password }),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }),
};

// ── Users ────────────────────────────────────────────────────────────────────
export const usersApi = {
  me: () => api.get<User>("/users/me"),
  updateMe: (body: Partial<Pick<User, "first_name" | "last_name" | "phone" | "langue">>) =>
    api.put<User>("/users/me", body),
  updateFcmToken: (fcm_token: string | null) =>
    api.patch("/users/me/fcm-token", { fcm_token }),
  myPlafond: () => api.get<PlafondStatus>("/users/me/plafond"),
  list: (params: { page?: number; page_size?: number; search?: string; role?: string }) => {
    const q = new URLSearchParams();
    if (params.page) q.set("page", String(params.page));
    if (params.page_size) q.set("page_size", String(params.page_size));
    if (params.search) q.set("search", params.search);
    if (params.role) q.set("role", params.role);
    return api.get<PaginatedResponse<User>>(`/users?${q}`);
  },
  get: (id: number) => api.get<User>(`/users/${id}`),
  create: (body: Record<string, unknown>) => api.post<User>("/users", body),
  update: (id: number, body: Record<string, unknown>) => api.put<User>(`/users/${id}`, body),
  toggle: (id: number) => api.patch<User>(`/users/${id}/toggle`),
  resetPassword: (id: number) => api.patch(`/users/${id}/reset-password`),
  updatePlafond: (id: number, plafond_mensuel: number | null) =>
    api.patch<User>(`/users/${id}/plafond`, { plafond_mensuel }),
  updateRole: (id: number, role: string) => api.patch<User>(`/users/${id}/role`, { role }),
  updatePaymentMode: (id: number, payment_mode: string) =>
    api.patch<User>(`/users/${id}/payment-mode`, { payment_mode }),
  plafondStatus: (id: number) => api.get<PlafondStatus>(`/users/${id}/plafond/status`),
  orders: (id: number, page = 1) =>
    api.get<PaginatedResponse<Order>>(`/users/${id}/orders?page=${page}`),
};

// ── Products ─────────────────────────────────────────────────────────────────
export const productsApi = {
  list: (params: URLSearchParams) => api.get<PaginatedResponse<Product>>(`/products?${params}`),
  mobileList: (params: URLSearchParams) =>
    api.get<PaginatedResponse<ProductMobile>>(`/products/mobile?${params}`),
  search: (q: string, page = 1) =>
    api.get<PaginatedResponse<Product>>(`/products/search?q=${encodeURIComponent(q)}&page=${page}`),
  get: (id: number) => api.get<Product>(`/products/${id}`),
  mobileGet: (id: number) => api.get<ProductMobile>(`/products/mobile/${id}`),
  byCode: (code: string) => api.get<Product>(`/products/by-code/${encodeURIComponent(code)}`),
  mobileByCode: (code: string) =>
    api.get<ProductMobile>(`/products/mobile/by-code/${encodeURIComponent(code)}`),
  exportUncategorized: () =>
    api.get<Blob>("/products/export/uncategorized", { responseType: "blob" }),
  gammes: () => api.get<string[]>("/products/gammes"),
  familles: () => api.get<string[]>("/products/familles"),
  sousFamilles: () => api.get<string[]>("/products/sous-familles"),
  categories: () => api.get<string[]>("/products/categories"),
  sousCategories: () => api.get<string[]>("/products/sous-categories"),
  societes: () => api.get<string[]>("/products/societes"),
  create: (body: Record<string, unknown>) => api.post<Product>("/products", body),
  update: (id: number, body: Record<string, unknown>) => api.put<Product>(`/products/${id}`, body),
  toggle: (id: number) => api.patch<Product>(`/products/${id}/toggle`),
  assign: (
    id: number,
    body: {
      gamme?: string | null;
      famille?: string | null;
      sous_famille?: string | null;
      categorie?: string | null;
      sous_categorie?: string | null;
    },
  ) => api.post<Product>(`/products/${id}/assign`, body),
  bulkAssign: (body: {
    product_ids: number[];
    gamme?: string | null;
    famille?: string | null;
    sous_famille?: string | null;
    categorie?: string | null;
    sous_categorie?: string | null;
  }) => api.post<{ updated: number }>("/products/bulk-assign", body),
  uploadImage: (id: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<Product>(`/products/${id}/image`, fd);
  },
  deleteImage: (id: number) => api.delete(`/products/${id}/image`),
};

// ── Orders ───────────────────────────────────────────────────────────────────
export const ordersApi = {
  list: (page: number, status?: string) => {
    const q = new URLSearchParams({ page: String(page) });
    if (status) q.set("status", status);
    return api.get<PaginatedResponse<Order>>(`/orders?${q}`);
  },
  myList: (page: number, status?: string) => {
    const q = new URLSearchParams({ page: String(page) });
    if (status) q.set("status", status);
    return api.get<PaginatedResponse<Order>>(`/orders/me?${q}`);
  },
  create: (lines: { product_code: string; quantity: number }[], notes?: string) =>
    api.post<Order[]>("/orders", { lines, notes }),
  get: (id: number) => api.get<Order>(`/orders/${id}`),
  lines: (id: number) => api.get<OrderLine[]>(`/orders/${id}/lines`),
  statusHistory: (id: number) => api.get<OrderStatusHistory[]>(`/orders/${id}/status-history`),
  bl: (id: number) => api.get<Order>(`/orders/${id}/bl`),
  cancel: (id: number) => api.patch<Order>(`/orders/${id}/cancel`),
  updateStatus: (id: number, status: string, notes?: string) =>
    api.patch<Order>(`/orders/${id}/status`, { status, notes }),
  validate: (id: number) => api.patch<Order>(`/orders/${id}/validate`),
};

// ── Annuaire ───────────────────────────────────────────────────────────────────
export const annuaireApi = {
  list: (page: number, search?: string) => {
    const q = new URLSearchParams({ page: String(page) });
    if (search) q.set("search", search);
    return api.get<PaginatedResponse<AnnuaireEntry>>(`/annuaire?${q}`);
  },
  get: (id: number) => api.get<AnnuaireEntry>(`/annuaire/${id}`),
};

// ── Banners ──────────────────────────────────────────────────────────────────
export const bannersApi = {
  list: (includeInactive = false) =>
    api.get<Banner[]>(`/banners${includeInactive ? "?include_inactive=true" : ""}`),
  get: (id: number) => api.get<Banner>(`/banners/${id}`),
  update: (id: number, body: { title?: string; subtitle?: string; link_url?: string }) =>
    api.put<Banner>(`/banners/${id}`, body),
  toggle: (id: number) => api.patch<Banner>(`/banners/${id}/toggle`),
  uploadImage: (id: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<Banner>(`/banners/${id}/image`, fd);
  },
};

// ── Notifications ────────────────────────────────────────────────────────────
export const notificationsApi = {
  list: (page = 1, page_size = 20) =>
    api.get<PaginatedResponse<Notification>>(`/notifications?page=${page}&page_size=${page_size}`),
  unreadCount: () => api.get<{ unread_count: number }>("/notifications/unread-count"),
  markRead: (id: number) => api.patch<Notification>(`/notifications/${id}/read`),
  markAllRead: () => api.patch("/notifications/read-all"),
  send: (body: { user_id: number; title: string; body: string; type?: string }) =>
    api.post<Notification>("/notifications/send", body),
  delete: (id: number) => api.delete(`/notifications/${id}`),
};

// ── Payment methods ──────────────────────────────────────────────────────────
// Note: PATCH /payment-methods/me was removed (CDC §3.4: admin sets modes, not the user).
// Users view their mode via GET /payment-methods; admin changes it via setUserMode.
export const paymentMethodsApi = {
  mine: () => api.get<string[]>("/payment-methods"),
  allModes: () => api.get<string[]>("/payment-methods/all"),
  setUserMode: (userId: number, mode: string) =>
    api.patch(`/payment-methods/${userId}/${mode}/toggle`),
};

// ── Dashboard ──────────────────────────────────────────────────────────────────
export const dashboardApi = {
  get: () => api.get<DashboardData>("/dashboard"),
};

// ── Sync (admin web) ───────────────────────────────────────────────────────────
export interface SyncLog {
  id: number;
  entity_type: string;
  operation: string;
  status: string;
  records_processed: number;
  records_failed: number;
  error_message: string | null;
  started_at: string;
  ended_at: string | null;
}

export interface SyncOverview {
  db: string;
  app_version: string;
  last_sync: Record<
    string,
    {
      status: string;
      operation: string;
      records_processed: number;
      records_failed: number;
      started_at: string;
    }
  >;
}

// ── Catalog / référentiels (additive — does not replace /products/gammes) ─────
export const catalogApi = {
  gammes: (includeInactive = false) =>
    api.get<CatalogGamme[]>(`/catalog/gammes?include_inactive=${includeInactive}`),
  createGamme: (name: string) => api.post<CatalogGamme>("/catalog/gammes", { name }),
  updateGamme: (id: number, body: Partial<CatalogGamme>) => api.put<CatalogGamme>(`/catalog/gammes/${id}`, body),

  familles: (gammeId?: number, includeInactive = false) => {
    const q = new URLSearchParams({ include_inactive: String(includeInactive) });
    if (gammeId != null) q.set("gamme_id", String(gammeId));
    return api.get<CatalogFamille[]>(`/catalog/familles?${q}`);
  },
  createFamille: (gamme_id: number, name: string) =>
    api.post<CatalogFamille>("/catalog/familles", { gamme_id, name }),
  updateFamille: (id: number, body: Partial<CatalogFamille>) =>
    api.put<CatalogFamille>(`/catalog/familles/${id}`, body),

  sousFamilles: (familleId?: number, includeInactive = false) => {
    const q = new URLSearchParams({ include_inactive: String(includeInactive) });
    if (familleId != null) q.set("famille_id", String(familleId));
    return api.get<CatalogSousFamille[]>(`/catalog/sous-familles?${q}`);
  },
  createSousFamille: (famille_id: number, name: string) =>
    api.post<CatalogSousFamille>("/catalog/sous-familles", { famille_id, name }),
  updateSousFamille: (id: number, body: Partial<CatalogSousFamille>) =>
    api.put<CatalogSousFamille>(`/catalog/sous-familles/${id}`, body),

  categories: (includeInactive = false) =>
    api.get<CatalogCategorie[]>(`/catalog/categories?include_inactive=${includeInactive}`),
  categoriesTree: (includeInactive = false) =>
    api.get<CatalogCategorieTreeNode[]>(`/catalog/categories/tree?include_inactive=${includeInactive}`),
  createCategorie: (name: string) => api.post<CatalogCategorie>("/catalog/categories", { name }),
  updateCategorie: (id: number, body: Partial<CatalogCategorie>) =>
    api.put<CatalogCategorie>(`/catalog/categories/${id}`, body),
  uploadCategorieImage: (id: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<CatalogCategorie>(`/catalog/categories/${id}/image`, fd);
  },
  deleteCategorieImage: (id: number) =>
    api.delete(`/catalog/categories/${id}/image`),

  sousCategories: (categorieId?: number, includeInactive = false) => {
    const q = new URLSearchParams({ include_inactive: String(includeInactive) });
    if (categorieId != null) q.set("categorie_id", String(categorieId));
    return api.get<CatalogSousCategorie[]>(`/catalog/sous-categories?${q}`);
  },
  createSousCategorie: (categorie_id: number, name: string) =>
    api.post<CatalogSousCategorie>("/catalog/sous-categories", { categorie_id, name }),
  updateSousCategorie: (id: number, body: Partial<CatalogSousCategorie>) =>
    api.put<CatalogSousCategorie>(`/catalog/sous-categories/${id}`, body),

  types: (sousCategorieId?: number, includeInactive = false) => {
    const q = new URLSearchParams({ include_inactive: String(includeInactive) });
    if (sousCategorieId != null) q.set("sous_categorie_id", String(sousCategorieId));
    return api.get<CatalogType[]>(`/catalog/types?${q}`);
  },
  createType: (sous_categorie_id: number, name: string) =>
    api.post<CatalogType>("/catalog/types", { sous_categorie_id, name }),
  updateType: (id: number, body: Partial<CatalogType>) =>
    api.put<CatalogType>(`/catalog/types/${id}`, body),

  reorderCategories: (ids: number[]) =>
    api.put<{ updated: number }>("/catalog/reorder/categories", { ids }),
  reorderSousCategories: (categorieId: number, ids: number[]) =>
    api.put<{ updated: number }>(`/catalog/reorder/sous-categories?categorie_id=${categorieId}`, { ids }),
  reorderTypes: (sousCategorieId: number, ids: number[]) =>
    api.put<{ updated: number }>(`/catalog/reorder/types?sous_categorie_id=${sousCategorieId}`, { ids }),
  reorderProducts: (ids: number[]) =>
    api.put<{ updated: number }>("/catalog/reorder/products", { ids }),

  societes: (includeInactive = false) =>
    api.get<OrgSociete[]>(`/catalog/societes?include_inactive=${includeInactive}`),
  createSociete: (code: string, label: string) =>
    api.post<OrgSociete>("/catalog/societes", { code, label }),
  updateSociete: (id: number, body: Partial<OrgSociete>) =>
    api.put<OrgSociete>(`/catalog/societes/${id}`, body),

  agences: (societeId?: number, includeInactive = false) => {
    const q = new URLSearchParams({ include_inactive: String(includeInactive) });
    if (societeId != null) q.set("societe_id", String(societeId));
    return api.get<OrgAgence[]>(`/catalog/agences?${q}`);
  },
  createAgence: (societe_id: number, code: string, label: string) =>
    api.post<OrgAgence>("/catalog/agences", { societe_id, code, label }),
  updateAgence: (id: number, body: Partial<OrgAgence>) =>
    api.put<OrgAgence>(`/catalog/agences/${id}`, body),

  villes: (includeInactive = false) =>
    api.get<OrgVille[]>(`/catalog/villes?include_inactive=${includeInactive}`),
  createVille: (code: string, label: string) =>
    api.post<OrgVille>("/catalog/villes", { code, label }),
  updateVille: (id: number, body: Partial<OrgVille>) =>
    api.put<OrgVille>(`/catalog/villes/${id}`, body),

  importFromData: () => api.post("/catalog/import-from-data"),
};

export const syncApi = {
  overview: () => api.get<SyncOverview>("/sync/overview"),
  logs: (page = 1, entity_type?: string) => {
    const q = new URLSearchParams({ page: String(page) });
    if (entity_type) q.set("entity_type", entity_type);
    return api.get<PaginatedResponse<SyncLog>>(`/sync/logs?${q}`);
  },
  rotateToken: () => api.post<TokenRotateResponse>("/sync/tokens/rotate"),
};
