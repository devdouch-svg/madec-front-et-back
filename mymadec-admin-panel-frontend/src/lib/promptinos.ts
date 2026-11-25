import { productsApi } from "./api/services";

/** ERP gamme name — products with this `gamme` appear on the Promptinos page. */
export const PROMPTINOS_GAMME = "Promptinos";

export const PROMPTINOS_META = {
  title: "Promptinos",
  tagline: "Notre sélection signature",
  description:
    "Découvrez la gamme Promptinos — produits phares, promotions et liquidations regroupés pour commander en un clin d'œil.",
} as const;

export const PROMPTINOS_PAGE_SIZE = 24;

export type PromptinosView = "all" | "promos" | "liquidations";

export interface PromptinosListFilters {
  page?: number;
  pageSize?: number;
  famille?: string;
  search?: string;
  view?: PromptinosView;
}

/** Build query params for `GET /products` (Promptinos scope). */
export function promptinosListParams({
  page = 1,
  pageSize = PROMPTINOS_PAGE_SIZE,
  famille = "",
  search = "",
  view = "all",
}: PromptinosListFilters = {}): URLSearchParams {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (view === "promos") {
    params.set("has_discount", "true");
  } else if (view === "liquidations") {
    params.set("is_liquidation", "true");
  } else {
    params.set("gamme", PROMPTINOS_GAMME);
    params.set("include_liquidations", "true");
  }
  if (famille) params.set("famille", famille);
  if (search.trim().length >= 2) params.set("search", search.trim());
  return params;
}

export function promptinosProductsUrl(gammeOnly = true): string {
  const params = new URLSearchParams({ gamme: PROMPTINOS_GAMME });
  return gammeOnly ? `/products?${params}` : "/promptinos";
}

export interface PromptinosStats {
  total: number;
  promoTotal: number;
  liquidationTotal: number;
}

/** Shared stats fetcher for React Query (`queryKey: ["promptinos", "stats"]`). */
export async function fetchPromptinosStats(): Promise<PromptinosStats> {
  const [all, promos, liquidations] = await Promise.all([
    productsApi.list(promptinosListParams({ page: 1, pageSize: 1, view: "all" })),
    productsApi.list(promptinosListParams({ page: 1, pageSize: 1, view: "promos" })),
    productsApi.list(promptinosListParams({ page: 1, pageSize: 1, view: "liquidations" })),
  ]);
  return {
    total: all.data.total,
    promoTotal: promos.data.total,
    liquidationTotal: liquidations.data.total,
  };
}
