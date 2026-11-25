import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Package,
  Search,
  ShoppingCart,
  Sparkles,
  Tag,
  ArrowRight,
  X,
  Loader2,
  ExternalLink,
  Flame,
} from "lucide-react";
import toast from "react-hot-toast";
import { PROMPTINOS_META, promptinosProductsUrl, type PromptinosView } from "../lib/promptinos";
import type { Product } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { Pagination } from "../components/ui/Pagination";
import { Modal } from "../components/ui/Modal";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { ProductPrice } from "../components/products/ProductPrice";
import { PromptinosProductCard } from "../components/promptinos/PromptinosProductCard";
import { useCart } from "../store/cart";
import { useRole } from "../lib/roles";
import { usePromptinosCatalog } from "../hooks/usePromptinos";
import { mediaUrl } from "../lib/media";

function readInt(value: string | null, fallback: number) {
  const n = Number(value);
  return Number.isFinite(n) && n >= 1 ? n : fallback;
}

function readView(searchParams: URLSearchParams): PromptinosView {
  const view = searchParams.get("view");
  if (view === "promos" || view === "liquidations") return view;
  if (searchParams.get("promos") === "1") return "promos";
  return "all";
}

export function PromptinosPage() {
  const { add, items } = useCart();
  const { isAcheteur, isAdminOrGest } = useRole();
  const [searchParams, setSearchParams] = useSearchParams();

  const [page, setPage] = useState(() => readInt(searchParams.get("page"), 1));
  const [search, setSearch] = useState(() => searchParams.get("q") ?? "");
  const [view, setView] = useState<PromptinosView>(() => readView(searchParams));
  const [viewProduct, setViewProduct] = useState<Product | null>(null);

  const { debouncedSearch, isSearching, isInitialLoading, data, isError, refetch, isFetching, stats } =
    usePromptinosCatalog({ page, search, view });

  const cartQtyById = useMemo(() => {
    const map = new Map<number, number>();
    for (const item of items) map.set(item.product.id, item.quantity);
    return map;
  }, [items]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (page > 1) params.set("page", String(page));
    if (search) params.set("q", search);
    if (view !== "all") params.set("view", view);
    setSearchParams(params, { replace: true });
  }, [page, search, view, setSearchParams]);

  const resetFilters = useCallback(() => {
    setSearch("");
    setView("all");
    setPage(1);
  }, []);

  if (isInitialLoading) return <PageLoader />;

  const hasFilters = !!(search || view !== "all");
  const activeFilterCount = [search, view !== "all"].filter(Boolean).length;
  const viewLabel =
    view === "promos" ? "en promotion" : view === "liquidations" ? "en liquidation" : "";

  return (
    <div className="page-content max-w-7xl space-y-6">
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-950 via-primary-700 to-primary-500 text-white shadow-lg">
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/10 blur-2xl" aria-hidden />
        <div className="pointer-events-none absolute -bottom-20 left-1/3 h-48 w-48 rounded-full bg-primary-400/20 blur-3xl" aria-hidden />
        <div className="relative flex flex-col gap-6 p-6 md:flex-row md:items-end md:justify-between md:p-8">
          <div className="max-w-xl">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide backdrop-blur-sm">
              <Sparkles size={14} />
              Gamme dédiée
            </span>
            <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">{PROMPTINOS_META.title}</h1>
            <p className="mt-1 text-sm font-medium text-primary-100">{PROMPTINOS_META.tagline}</p>
            <p className="mt-3 text-sm leading-relaxed text-primary-50/90 md:text-base">
              {PROMPTINOS_META.description}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-3">
            <div className="rounded-xl bg-white/10 px-4 py-3 backdrop-blur-sm ring-1 ring-white/20">
              <p className="text-2xl font-bold">{stats?.total ?? data?.total ?? 0}</p>
              <p className="text-xs text-primary-100">produits</p>
            </div>
            {(stats?.promoTotal ?? 0) > 0 && (
              <div className="rounded-xl bg-amber-400/20 px-4 py-3 backdrop-blur-sm ring-1 ring-amber-200/30">
                <p className="text-2xl font-bold text-amber-100">{stats!.promoTotal}</p>
                <p className="text-xs text-amber-100/90">promos</p>
              </div>
            )}
            {(stats?.liquidationTotal ?? 0) > 0 && (
              <div className="rounded-xl bg-rose-400/20 px-4 py-3 backdrop-blur-sm ring-1 ring-rose-200/30">
                <p className="text-2xl font-bold text-rose-100">{stats!.liquidationTotal}</p>
                <p className="text-xs text-rose-100/90">liquidations</p>
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative min-w-48 flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
          <input
            className="input pl-9 pr-9"
            placeholder="Rechercher dans Promptinos…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            aria-label="Rechercher un produit Promptinos"
          />
          {(isSearching || (isFetching && !isInitialLoading)) && (
            <Loader2
              size={16}
              className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-madec-muted"
              aria-hidden
            />
          )}
        </div>
        <button
          type="button"
          onClick={() => {
            setView((v) => (v === "promos" ? "all" : "promos"));
            setPage(1);
          }}
          className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
            view === "promos"
              ? "border-amber-300 bg-amber-50 text-amber-800"
              : "border-madec-border bg-white text-madec-secondary hover:bg-madec-surface"
          }`}
        >
          <Tag size={16} />
          Promotions
          {(stats?.promoTotal ?? 0) > 0 && (
            <span className="rounded-full bg-amber-200/80 px-1.5 text-[10px] font-bold text-amber-900">
              {stats!.promoTotal}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => {
            setView((v) => (v === "liquidations" ? "all" : "liquidations"));
            setPage(1);
          }}
          className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
            view === "liquidations"
              ? "border-rose-300 bg-rose-50 text-rose-800"
              : "border-madec-border bg-white text-madec-secondary hover:bg-madec-surface"
          }`}
        >
          <Flame size={16} />
          Liquidations
          {(stats?.liquidationTotal ?? 0) > 0 && (
            <span className="rounded-full bg-rose-200/80 px-1.5 text-[10px] font-bold text-rose-900">
              {stats!.liquidationTotal}
            </span>
          )}
        </button>
        {isAdminOrGest && (
          <Link to={promptinosProductsUrl()} className="btn-secondary whitespace-nowrap">
            Gérer dans Produits
            <ExternalLink size={16} />
          </Link>
        )}
        <Link to="/products" className="btn-secondary whitespace-nowrap">
          Tout le catalogue
          <ArrowRight size={16} />
        </Link>
      </div>

      {hasFilters && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-madec-muted">
            {activeFilterCount} filtre{activeFilterCount > 1 ? "s" : ""} actif{activeFilterCount > 1 ? "s" : ""}
          </span>
          {search && (
            <span className="inline-flex items-center gap-1 rounded-full bg-madec-tint px-2.5 py-1 text-xs text-madec-text">
              « {search} »
              <button type="button" onClick={() => { setSearch(""); setPage(1); }} aria-label="Retirer la recherche">
                <X size={12} />
              </button>
            </span>
          )}
          {view === "promos" && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs text-amber-800 ring-1 ring-amber-200">
              Promotions
              <button type="button" onClick={() => { setView("all"); setPage(1); }} aria-label="Retirer le filtre promos">
                <X size={12} />
              </button>
            </span>
          )}
          {view === "liquidations" && (
            <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs text-rose-800 ring-1 ring-rose-200">
              Liquidations
              <button type="button" onClick={() => { setView("all"); setPage(1); }} aria-label="Retirer le filtre liquidations">
                <X size={12} />
              </button>
            </span>
          )}
          <button type="button" onClick={resetFilters} className="text-xs font-medium text-madec-primary hover:underline">
            Tout effacer
          </button>
        </div>
      )}

      {debouncedSearch.length > 0 && debouncedSearch.length < 2 && (
        <p className="text-xs text-madec-muted">Saisissez au moins 2 caractères pour lancer la recherche.</p>
      )}

      {isError && <ErrorState onRetry={() => refetch()} />}

      {!isError && data && data.items.length === 0 && (
        <EmptyState
          icon={Sparkles}
          title="Aucun produit Promptinos"
          description={
            hasFilters
              ? "Essayez d'autres filtres ou élargissez votre recherche."
              : `Les produits Promptinos et les liquidations apparaîtront ici. Consultez le catalogue complet en attendant.`
          }
          action={
            hasFilters ? (
              <button type="button" onClick={resetFilters} className="btn-secondary mt-4">
                Réinitialiser les filtres
              </button>
            ) : (
              <Link to="/products" className="btn-primary mt-4">
                Voir le catalogue
              </Link>
            )
          }
        />
      )}

      {!isError && data && data.items.length > 0 && (
        <>
          <p className="text-sm text-madec-muted">
            {data.total} produit{data.total > 1 ? "s" : ""}
            {viewLabel ? ` ${viewLabel}` : ""}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {data.items.map((product) => (
              <PromptinosProductCard
                key={product.id}
                product={product}
                cartQty={cartQtyById.get(product.id) ?? 0}
                showCart={isAcheteur}
                showStaffBadge={isAdminOrGest}
                onView={setViewProduct}
                onAddToCart={(p) => {
                  add(p);
                  toast.success("Ajouté au panier");
                }}
              />
            ))}
          </div>
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            pageSize={data.page_size}
            onChange={setPage}
          />
        </>
      )}

      <Modal
        open={viewProduct != null}
        onClose={() => setViewProduct(null)}
        title={viewProduct?.name ?? "Produit"}
        size="lg"
      >
        {viewProduct && (
          <div className="grid gap-6 md:grid-cols-2">
            {viewProduct.image_path ? (
              <img
                src={mediaUrl(viewProduct.image_path, viewProduct.updated_at)}
                alt=""
                className="w-full rounded-xl object-cover md:max-h-72"
              />
            ) : (
              <div className="flex aspect-square max-h-72 items-center justify-center rounded-xl bg-madec-tint text-madec-muted/50">
                <Package size={48} strokeWidth={1.25} />
              </div>
            )}
            <div className="space-y-3 text-sm">
              <p className="font-mono text-xs text-madec-muted">{viewProduct.product_code}</p>
              {viewProduct.description && <p className="text-madec-secondary">{viewProduct.description}</p>}
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <dt className="text-madec-muted">Unité</dt>
                  <dd className="font-medium">{viewProduct.unit ?? "—"}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-madec-muted">Prix</dt>
                  <dd>
                    <ProductPrice
                      basePrice={viewProduct.base_price}
                      finalPrice={viewProduct.final_price}
                      discountRate={viewProduct.discount_rate}
                      unit={viewProduct.unit}
                      size="lg"
                    />
                  </dd>
                </div>
              </dl>
              {isAcheteur && (
                <button
                  type="button"
                  className="btn-primary w-full"
                  disabled={!viewProduct.is_active}
                  onClick={() => {
                    add(viewProduct);
                    toast.success("Ajouté au panier");
                    setViewProduct(null);
                  }}
                >
                  <ShoppingCart size={16} />
                  Ajouter au panier
                </button>
              )}
              {isAdminOrGest && (
                <Link to={promptinosProductsUrl()} className="btn-secondary w-full">
                  Gérer dans le catalogue staff
                </Link>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
