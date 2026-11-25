import { useState, useRef, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { Search, Plus, ScanLine, Package, CheckSquare, Square, Download, Sparkles } from "lucide-react";
import { PROMPTINOS_GAMME } from "../lib/promptinos";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { PaginatedResponse, Product } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { Pagination } from "../components/ui/Pagination";
import { Modal } from "../components/ui/Modal";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { useCart } from "../store/cart";
import { useRole } from "../lib/roles";
import { staffCan, staffPageScope } from "../lib/staffCapabilities";
import toast from "react-hot-toast";
import { ProductCatalogCard } from "../components/products/ProductCatalogCard";
import { ProductFormModal } from "../components/products/ProductFormModal";
import { ProductPrice } from "../components/products/ProductPrice";
import { StatusBadge } from "../components/ui/StatusBadge";
import { productsApi } from "../lib/api/services";
import { mediaUrl } from "../lib/media";
import { CatalogSelect } from "../components/ui/CatalogSelect";
import { useDebounce } from "../hooks/useDebounce";
import {
  findCategorieId,
  useCatalogCategories,
  useCatalogFamilles,
  useCatalogGammes,
  useCatalogSocietes,
  useCatalogSousCategories,
  useCatalogSousFamilles,
} from "../hooks/useCatalog";

export function ProductsPage() {
  const { add } = useCart();
  const qc = useQueryClient();
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});
  const [searchParams, setSearchParams] = useSearchParams();

  const [page, setPage]       = useState(1);
  const [search, setSearch]   = useState(() => searchParams.get("search") ?? "");
  const debouncedSearch = useDebounce(search, 3000);
  const [gamme, setGamme]     = useState("");
  const [famille, setFamille] = useState("");
  const [sousFamille, setSousFamille] = useState("");
  const [categorie, setCategorie] = useState(() => searchParams.get("categorie") ?? "");
  const [sousCategorie, setSousCategorie] = useState(() => searchParams.get("sous_categorie") ?? "");
  const [uncategorizedMobile, setUncategorizedMobile] = useState(
    () => searchParams.get("missing_mobile_category") === "true",
  );
  const [societe, setSociete] = useState("");
  const [barcode, setBarcode] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editProduct, setEditProduct] = useState<Product | null>(null);
  const [viewProductId, setViewProductId] = useState<number | null>(null);

  const { isAdmin, isAdminOrGest, isAcheteur, role } = useRole();
  const [inactiveOnly, setInactiveOnly] = useState(false);
  const [assignProduct, setAssignProduct] = useState<Product | null>(null);
  const [assignCategorie, setAssignCategorie] = useState("");
  const [assignSousCategorie, setAssignSousCategorie] = useState("");

  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(() => new Set());
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkCategorie, setBulkCategorie] = useState("");
  const [bulkSousCategorie, setBulkSousCategorie] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (categorie) params.set("categorie", categorie);
    if (sousCategorie) params.set("sous_categorie", sousCategorie);
    if (uncategorizedMobile) params.set("missing_mobile_category", "true");
    setSearchParams(params, { replace: true });
  }, [categorie, sousCategorie, uncategorizedMobile, setSearchParams]);

  const staffCatalog = isAdminOrGest;
  const syncFilters = isAdmin;

  const { data: gammes } = useQuery<string[]>({
    queryKey: ["gammes"],
    queryFn: () => api.get("/products/gammes").then((r) => r.data),
    enabled: syncFilters,
    staleTime: 5 * 60_000,
  });
  const { data: familles } = useQuery<string[]>({
    queryKey: ["familles"],
    queryFn: () => api.get("/products/familles").then((r) => r.data),
    enabled: syncFilters,
    staleTime: 5 * 60_000,
  });
  const { data: sousFamilles } = useQuery<string[]>({
    queryKey: ["sous-familles"],
    queryFn: () => api.get("/products/sous-familles").then((r) => r.data),
    enabled: syncFilters,
    staleTime: 5 * 60_000,
  });
  const { data: productCategories } = useQuery<string[]>({
    queryKey: ["categories"],
    queryFn: () => api.get("/products/categories").then((r) => r.data),
    enabled: staffCatalog,
    staleTime: 5 * 60_000,
  });
  const { data: societes } = useQuery<string[]>({
    queryKey: ["societes"],
    queryFn: () => api.get("/products/societes").then((r) => r.data),
    enabled: staffCatalog,
    staleTime: 5 * 60_000,
  });

  const { data: catalogGammes } = useCatalogGammes(false, staffCatalog);
  const { data: allCatalogFamilles } = useCatalogFamilles(null, false, staffCatalog);
  const { data: allCatalogSousFamilles } = useCatalogSousFamilles(null, false, staffCatalog);
  const { data: catalogSocietes } = useCatalogSocietes(false, staffCatalog);
  const { data: allCatalogCategories } = useCatalogCategories(false, true);
  const filterCategorieId = findCategorieId(allCatalogCategories, categorie);
  const { data: filterCatalogSousCategories } = useCatalogSousCategories(filterCategorieId, false, !!categorie);

  useEffect(() => {
    if (!categorie || !sousCategorie || !filterCatalogSousCategories) return;
    const allowed = new Set(filterCatalogSousCategories.map((s) => s.name));
    if (!allowed.has(sousCategorie)) setSousCategorie("");
  }, [categorie, sousCategorie, filterCatalogSousCategories]);

  const assignCategorieId = findCategorieId(allCatalogCategories, assignCategorie);
  const { data: assignCatalogSousCategories } = useCatalogSousCategories(assignCategorieId, false, !!assignProduct);

  const mergeOptions = (...lists: (string[] | undefined)[]) =>
    [...new Set(lists.flatMap((l) => l ?? []).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fr"));

  const filterGammes = mergeOptions(gammes, catalogGammes?.map((g) => g.name));
  const filterFamilles = mergeOptions(familles, allCatalogFamilles?.map((f) => f.name));
  const filterSousFamilles = mergeOptions(sousFamilles, allCatalogSousFamilles?.map((s) => s.name));
  const filterCategories = mergeOptions(productCategories, allCatalogCategories?.map((c) => c.name));
  const filterSousCategories = useMemo(() => {
    if (!categorie) return [];
    return (filterCatalogSousCategories?.map((s) => s.name) ?? [])
      .slice()
      .sort((a, b) => a.localeCompare(b, "fr"));
  }, [categorie, filterCatalogSousCategories]);
  const filterSocietes = mergeOptions(societes, catalogSocietes?.map((s) => s.code));

  const buildListUrl = () => {
    const params = new URLSearchParams({ page: String(page) });
    if (debouncedSearch.length >= 2) params.set("search", debouncedSearch);
    if (gamme) params.set("gamme", gamme);
    if (famille) params.set("famille", famille);
    if (sousFamille) params.set("sous_famille", sousFamille);
    if (categorie) params.set("categorie", categorie);
    if (sousCategorie) params.set("sous_categorie", sousCategorie);
    if (isAdminOrGest && uncategorizedMobile) params.set("missing_mobile_category", "true");
    if (societe) params.set("society_code", societe);
    if (isAdminOrGest && inactiveOnly) params.set("is_active", "false");
    return `/products?${params}`;
  };

  const { data, isLoading, isError, refetch } = useQuery<PaginatedResponse<Product>>({
    queryKey: ["products", page, debouncedSearch, gamme, famille, sousFamille, categorie, sousCategorie, uncategorizedMobile, societe, inactiveOnly],
    queryFn: () => api.get(buildListUrl()).then((r) => r.data),
  });

  const { data: viewProduct } = useQuery<Product>({
    queryKey: ["product", viewProductId],
    queryFn: () => api.get(`/products/${viewProductId}`).then((r) => r.data),
    enabled: viewProductId != null,
  });

  const toggle = useMutation({
    mutationFn: (id: number) => api.patch(`/products/${id}/toggle`),
    onSuccess: (res) => {
      const active = res.data?.is_active;
      toast.success(active ? "Produit activé" : "Produit désactivé");
      qc.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur lors du changement de statut")),
  });

  const uploadImage = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) => {
      const fd = new FormData();
      fd.append("file", file);
      return api.post(`/products/${id}/image`, fd);
    },
    onSuccess: () => { toast.success("Image mise à jour"); qc.invalidateQueries({ queryKey: ["products"] }); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur upload")),
  });

  const deleteImage = useMutation({
    mutationFn: (id: number) => api.delete(`/products/${id}/image`),
    onSuccess: () => { toast.success("Image supprimée"); qc.invalidateQueries({ queryKey: ["products"] }); },
  });

  const bulkCategorieId = findCategorieId(allCatalogCategories, bulkCategorie);
  const { data: bulkCatalogSousCategories } = useCatalogSousCategories(bulkCategorieId);

  const toggleSelected = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const pageIds = useMemo(() => data?.items.map((p) => p.id) ?? [], [data?.items]);
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id));

  const bulkAssign = useMutation({
    mutationFn: () =>
      productsApi.bulkAssign({
        product_ids: [...selectedIds],
        categorie: bulkCategorie || null,
        sous_categorie: bulkSousCategorie || null,
      }),
    onSuccess: (r) => {
      toast.success(`${r.data.updated} produit(s) mis à jour`);
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["catalog"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setSelectedIds(new Set());
      setSelectionMode(false);
      setBulkOpen(false);
      setBulkCategorie("");
      setBulkSousCategorie("");
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const assign = useMutation({
    mutationFn: ({ id, categorie, sous_categorie }: {
      id: number; categorie?: string; sous_categorie?: string;
    }) =>
      api.post(`/products/${id}/assign`, {
        categorie: categorie || null,
        sous_categorie: sous_categorie || null,
      }),
    onSuccess: () => {
      toast.success("Catégorie mobile assignée");
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["catalog"] });
      qc.invalidateQueries({ queryKey: ["categories"] });
      qc.invalidateQueries({ queryKey: ["sous-categories"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setAssignProduct(null);
      setAssignCategorie("");
      setAssignSousCategorie("");
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const scanProduct = useMutation({
    mutationFn: (code: string) => api.get(`/products/by-code/${encodeURIComponent(code)}`).then((r) => r.data),
    onSuccess: (product: Product) => {
      toast.success(`Trouvé : ${product.name}`);
      if (isAcheteur) add(product);
    },
    onError: () => toast.error("Produit introuvable"),
  });

  const exportUncategorized = async () => {
    try {
      const r = await productsApi.exportUncategorized();
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "produits-sans-categorie-mobile.csv";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export téléchargé");
    } catch (e) {
      toast.error(getErrorMessage(e, "Export impossible"));
    }
  };

  if (isLoading && !data) return <PageLoader />;

  const hasFilters = !!(search || gamme || famille || sousFamille || categorie || sousCategorie || uncategorizedMobile || societe || inactiveOnly);

  const clearFilters = () => {
    setSearch("");
    setGamme("");
    setFamille("");
    setSousFamille("");
    setCategorie("");
    setSousCategorie("");
    setUncategorizedMobile(false);
    setSociete("");
    setInactiveOnly(false);
    setBarcode("");
    setPage(1);
  };

  return (
    <div className="page-content max-w-7xl space-y-6">
      <PageHeader
        title="Catalogue produits"
        subtitle={staffPageScope("products", role) ?? "Parcourir et commander"}
        actions={
          isAdminOrGest ? (
            <div className="flex flex-wrap gap-2">
              <Link to="/promptinos" className="btn-secondary">
                <Sparkles size={16} />
                Promptinos
              </Link>
              {staffCan("export_uncategorized", role) && (
                <button type="button" className="btn-secondary" onClick={exportUncategorized}>
                  <Download size={16} />
                  Export sans catégorie
                </button>
              )}
              {staffCan("bulk_assign_mobile", role) && (
                <button
                  type="button"
                  className={selectionMode ? "btn-primary" : "btn-secondary"}
                  onClick={() => {
                    setSelectionMode((v) => !v);
                    setSelectedIds(new Set());
                  }}
                >
                  {selectionMode ? <CheckSquare size={16} /> : <Square size={16} />}
                  Sélection
                </button>
              )}
              {staffCan("manage_products", role) && (
                <button
                  type="button"
                  className="btn-primary"
                  disabled
                  title="Les produits sont ajoutés via la synchronisation ERP"
                >
                  <Plus size={16} /> Ajouter un produit
                </button>
              )}
            </div>
          ) : undefined
        }
      />

      {isAdmin && gamme !== PROMPTINOS_GAMME && filterGammes.includes(PROMPTINOS_GAMME) && (
        <Link
          to="/promptinos"
          className="flex items-center justify-between gap-3 rounded-xl border border-madec-tint bg-madec-active/60 px-4 py-3 text-sm transition-colors hover:bg-madec-active"
        >
          <span className="flex items-center gap-2 font-medium text-madec-text">
            <Sparkles size={16} className="text-madec-primary" />
            Parcourir la page dédiée Promptinos
          </span>
          <span className="text-xs text-madec-primary">Vue acheteur →</span>
        </Link>
      )}

      {isAdmin && gamme === PROMPTINOS_GAMME && (
        <div className="info-note flex flex-wrap items-center justify-between gap-2">
          <span className="flex items-center gap-2">
            <Sparkles size={16} className="text-madec-primary" />
            Filtre actif : gamme <strong>{PROMPTINOS_GAMME}</strong>
          </span>
          <Link to="/promptinos" className="link-brand text-sm">
            Ouvrir la page Promptinos
          </Link>
        </div>
      )}

      <div className="catalog-toolbar">
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative min-w-0 flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
            <input
              className="input pl-9"
              placeholder="Rechercher un produit..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <div className="flex gap-2 sm:max-w-sm sm:flex-1">
            <div className="relative min-w-0 flex-1">
              <ScanLine size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
              <input
                className="input pl-9"
                placeholder="Code-barres..."
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && barcode.trim()) scanProduct.mutate(barcode.trim()); }}
              />
            </div>
            <button
              type="button"
              className="btn-secondary btn-sm shrink-0"
              disabled={!barcode.trim() || scanProduct.isPending}
              onClick={() => scanProduct.mutate(barcode.trim())}
            >
              Scanner
            </button>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {isAdmin && (
            <>
              <select className="input" value={gamme} onChange={(e) => { setGamme(e.target.value); setPage(1); }}>
                <option value="">Toutes les gammes</option>
                {filterGammes.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
              <select className="input" value={famille} onChange={(e) => { setFamille(e.target.value); setPage(1); }}>
                <option value="">Toutes les familles</option>
                {filterFamilles.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
              <select className="input" value={sousFamille} onChange={(e) => { setSousFamille(e.target.value); setPage(1); }}>
                <option value="">Sous-familles</option>
                {filterSousFamilles.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </>
          )}
          <select className="input" value={categorie} onChange={(e) => { setCategorie(e.target.value); setSousCategorie(""); setUncategorizedMobile(false); setPage(1); }}>
            <option value="">Catégories mobile</option>
            {filterCategories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select
            className="input"
            value={sousCategorie}
            onChange={(e) => { setSousCategorie(e.target.value); setUncategorizedMobile(false); setPage(1); }}
            disabled={!categorie}
          >
            <option value="">Sous-catégories</option>
            {filterSousCategories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="input" value={societe} onChange={(e) => { setSociete(e.target.value); setPage(1); }}>
            <option value="">Sociétés</option>
            {filterSocietes.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {(isAdminOrGest || (selectionMode && data && data.items.length > 0)) && (
          <div className="flex flex-wrap items-center gap-3 border-t border-madec-border pt-3">
            {isAdminOrGest && (
              <label className="filter-chip flex cursor-pointer items-center gap-2 !py-2">
                <input
                  type="checkbox"
                  checked={uncategorizedMobile}
                  onChange={(e) => {
                    setUncategorizedMobile(e.target.checked);
                    if (e.target.checked) { setCategorie(""); setSousCategorie(""); }
                    setPage(1);
                  }}
                  className="rounded border-madec-border text-madec-primary"
                />
                Sans catégorie mobile
              </label>
            )}
            {isAdminOrGest && (
              <label className="filter-chip flex cursor-pointer items-center gap-2 !py-2">
                <input
                  type="checkbox"
                  checked={inactiveOnly}
                  onChange={(e) => { setInactiveOnly(e.target.checked); setPage(1); }}
                  className="rounded border-madec-border text-madec-primary"
                />
                Inactifs seulement
              </label>
            )}
            {isAdminOrGest && selectionMode && data && data.items.length > 0 && (
              <button
                type="button"
                className="filter-chip"
                onClick={() => {
                  if (allPageSelected) {
                    setSelectedIds((prev) => {
                      const next = new Set(prev);
                      pageIds.forEach((id) => next.delete(id));
                      return next;
                    });
                  } else {
                    setSelectedIds((prev) => new Set([...prev, ...pageIds]));
                  }
                }}
              >
                {allPageSelected ? "Désélectionner page" : "Sélectionner page"}
              </button>
            )}
          </div>
        )}
      </div>

      {isError && <ErrorState onRetry={() => refetch()} />}

      {!isError && data && data.items.length === 0 && (
        <EmptyState
          icon={Package}
          title="Aucun produit trouvé"
          description={hasFilters ? "Modifiez vos filtres ou votre recherche." : "Le catalogue est vide pour le moment."}
        />
      )}

      {!isError && data && data.items.length > 0 && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-madec-muted">
              <span className="font-semibold text-madec-text">{data.total}</span> produit{data.total > 1 ? "s" : ""}
              {hasFilters && " · filtres actifs"}
            </p>
            {hasFilters && (
              <button type="button" onClick={clearFilters} className="link-brand text-xs">
                Réinitialiser les filtres
              </button>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {data.items.map((product) => (
              <ProductCatalogCard
                key={product.id}
                product={product}
                selectionMode={selectionMode}
                selected={selectedIds.has(product.id)}
                isAdmin={isAdmin}
                isAdminOrGest={isAdminOrGest}
                isAcheteur={isAcheteur}
                onToggleSelect={() => toggleSelected(product.id)}
                onView={() => setViewProductId(product.id)}
                onEdit={() => { setEditProduct(product); setFormOpen(true); }}
                onAssign={() => {
                  setAssignProduct(product);
                  setAssignCategorie(product.categorie ?? "");
                  setAssignSousCategorie(product.sous_categorie ?? "");
                }}
                onToggleActive={() => toggle.mutate(product.id)}
                onAddToCart={() => { add(product); toast.success("Ajouté au panier"); }}
                onUploadImage={() => fileRefs.current[product.id]?.click()}
                onDeleteImage={() => deleteImage.mutate(product.id)}
                fileInputRef={(el) => { fileRefs.current[product.id] = el; }}
                onFileChange={(file) => uploadImage.mutate({ id: product.id, file })}
              />
            ))}
          </div>
        </>
      )}

      {!isError && data && data.items.length > 0 && (
        <Pagination page={data.page} pages={data.pages} total={data.total} pageSize={data.page_size} onChange={setPage} />
      )}

      {formOpen && (
        <ProductFormModal
          key={editProduct?.id ?? "new"}
          open={formOpen}
          onClose={() => { setFormOpen(false); setEditProduct(null); }}
          product={editProduct}
        />
      )}

      <Modal
        open={viewProductId != null}
        onClose={() => setViewProductId(null)}
        title={viewProduct?.name ?? "Détail produit"}
        size="lg"
        dense
      >
        {viewProduct && (
          <div className="flex flex-col gap-4 text-sm sm:flex-row sm:items-start">
            <div className="mx-auto w-full shrink-0 sm:mx-0 sm:w-44">
              {viewProduct.image_path ? (
                <img
                  src={mediaUrl(viewProduct.image_path, viewProduct.updated_at)}
                  alt={viewProduct.name}
                  className="h-40 w-full rounded-lg bg-madec-surface object-contain ring-1 ring-madec-border sm:h-44"
                />
              ) : (
                <div className="flex h-40 w-full items-center justify-center rounded-lg bg-madec-surface text-madec-muted ring-1 ring-madec-border sm:h-44">
                  <Package size={36} strokeWidth={1.25} />
                </div>
              )}
            </div>

            <div className="min-w-0 flex-1 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-madec-muted">{viewProduct.product_code}</span>
                <StatusBadge status={viewProduct.is_active ? "active" : "inactive"} />
              </div>

              <div>
                <p className="text-xs text-madec-muted">Prix</p>
                <ProductPrice
                  basePrice={viewProduct.base_price}
                  finalPrice={viewProduct.final_price}
                  discountRate={viewProduct.discount_rate}
                  unit={viewProduct.unit}
                  size="lg"
                />
              </div>

              {viewProduct.description && (
                <p className="line-clamp-3 text-xs leading-relaxed text-madec-secondary">
                  {viewProduct.description}
                </p>
              )}

              <div className="grid grid-cols-2 gap-x-3 gap-y-2 border-t border-madec-border pt-3 text-xs">
                <div><span className="text-madec-muted">Remise</span><p className="font-medium">{viewProduct.discount_rate}%</p></div>
                <div><span className="text-madec-muted">Unité</span><p className="font-medium">{viewProduct.unit ?? "—"}</p></div>
                <div><span className="text-madec-muted">Type</span><p className="font-medium">{viewProduct.type_produit ?? "—"}</p></div>
                <div><span className="text-madec-muted">Gamme</span><p className="font-medium">{viewProduct.gamme ?? "—"}</p></div>
                <div><span className="text-madec-muted">Famille</span><p className="font-medium">{viewProduct.famille ?? "—"}</p></div>
                <div><span className="text-madec-muted">Sous-fam.</span><p className="font-medium">{viewProduct.sous_famille ?? "—"}</p></div>
                <div><span className="text-madec-muted">Catégorie</span><p className="font-medium">{viewProduct.categorie ?? "—"}</p></div>
                <div><span className="text-madec-muted">Sous-cat.</span><p className="font-medium">{viewProduct.sous_categorie ?? "—"}</p></div>
                <div><span className="text-madec-muted">PSG</span><p className="font-medium">{viewProduct.productsalesgroup_code ?? "—"}</p></div>
                <div className="col-span-2"><span className="text-madec-muted">Société</span><p className="font-medium">{viewProduct.society_code ?? "—"}</p></div>
              </div>

              {isAdminOrGest && (
                <div className="flex justify-end border-t border-madec-border pt-3">
                  <button
                    type="button"
                    className="btn-secondary btn-sm"
                    onClick={() => { setEditProduct(viewProduct); setFormOpen(true); setViewProductId(null); }}
                  >
                    Modifier
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

      <Modal open={!!assignProduct} onClose={() => setAssignProduct(null)} title="Assigner le catalogue">
        {assignProduct && (
          <div className="space-y-3">
            <p className="text-sm text-madec-secondary">{assignProduct.name}</p>
            <p className="text-xs text-madec-muted">
              Gamme, famille et sous-famille proviennent de la synchronisation ERP et ne sont pas modifiables ici.
            </p>
            <div className="grid grid-cols-3 gap-3 rounded-lg border border-madec-border bg-madec-surface px-3 py-2 text-sm">
              <div>
                <p className="text-xs text-madec-muted">Gamme</p>
                <p className="font-medium text-madec-text">{assignProduct.gamme ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-madec-muted">Famille</p>
                <p className="font-medium text-madec-text">{assignProduct.famille ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-madec-muted">Sous-famille</p>
                <p className="font-medium text-madec-text">{assignProduct.sous_famille ?? "—"}</p>
              </div>
            </div>
            <p className="text-xs font-medium text-madec-muted pt-1">Application mobile</p>
            <div>
              <label className="label">Catégorie</label>
              <CatalogSelect
                id="assign-categorie"
                value={assignCategorie}
                onChange={(v) => { setAssignCategorie(v); setAssignSousCategorie(""); }}
                options={allCatalogCategories?.map((c) => c.name) ?? []}
                placeholder="Choisir une catégorie"
              />
            </div>
            <div>
              <label className="label">Sous-catégorie</label>
              <CatalogSelect
                id="assign-sous-categorie"
                value={assignSousCategorie}
                onChange={setAssignSousCategorie}
                options={assignCatalogSousCategories?.map((s) => s.name) ?? []}
                placeholder="Choisir une sous-catégorie"
                disabled={!assignCategorie}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setAssignProduct(null)} className="btn-secondary">Annuler</button>
              <button
                onClick={() => assign.mutate({
                  id: assignProduct.id,
                  categorie: assignCategorie,
                  sous_categorie: assignSousCategorie,
                })}
                disabled={assign.isPending || (!assignCategorie && !assignSousCategorie)}
                className="btn-primary"
              >
                Assigner
              </button>
            </div>
          </div>
        )}
      </Modal>

      {selectionMode && selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-xl border border-madec-border bg-white px-4 py-3 shadow-lg">
          <span className="text-sm font-medium text-madec-text">{selectedIds.size} sélectionné(s)</span>
          <button type="button" className="btn-secondary btn-sm" onClick={() => setSelectedIds(new Set())}>
            Effacer
          </button>
          <button type="button" className="btn-primary btn-sm" onClick={() => setBulkOpen(true)}>
            Assigner catégorie mobile
          </button>
        </div>
      )}

      <Modal open={bulkOpen} onClose={() => setBulkOpen(false)} title={`Assigner ${selectedIds.size} produit(s)`}>
        <div className="space-y-3">
          <p className="text-xs text-madec-muted">Application mobile uniquement — les champs sync ERP ne sont pas modifiés.</p>
          <div>
            <label className="label">Catégorie</label>
            <CatalogSelect
              id="bulk-categorie"
              value={bulkCategorie}
              onChange={(v) => { setBulkCategorie(v); setBulkSousCategorie(""); }}
              options={allCatalogCategories?.map((c) => c.name) ?? []}
              placeholder="Choisir une catégorie"
            />
          </div>
          <div>
            <label className="label">Sous-catégorie</label>
            <CatalogSelect
              id="bulk-sous-categorie"
              value={bulkSousCategorie}
              onChange={setBulkSousCategorie}
              options={bulkCatalogSousCategories?.map((s) => s.name) ?? []}
              placeholder="Choisir une sous-catégorie"
              disabled={!bulkCategorie}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setBulkOpen(false)} className="btn-secondary">Annuler</button>
            <button
              type="button"
              className="btn-primary"
              disabled={bulkAssign.isPending || (!bulkCategorie && !bulkSousCategorie)}
              onClick={() => bulkAssign.mutate()}
            >
              {bulkAssign.isPending ? "..." : "Appliquer"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
