import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, GripVertical, Layers } from "lucide-react";
import toast from "react-hot-toast";
import { PageHeader } from "../components/layout/PageHeader";
import { PageLoader } from "../components/ui/Spinner";
import { StaffScopeBanner } from "../components/staff/StaffScopeBanner";
import { useRole } from "../lib/roles";
import { staffPageScope } from "../lib/staffCapabilities";
import { catalogApi, productsApi } from "../lib/api/services";
import { getErrorMessage } from "../lib/errors";
import { useCatalogCategories, useCatalogSousCategories, useCatalogTypes } from "../hooks/useCatalog";
import type { PaginatedResponse, Product } from "../lib/types";

type SortRow = {
  id: number;
  title: string;
  subtitle?: string;
};

export function CatalogSortPage() {
  const qc = useQueryClient();
  const { role } = useRole();
  const [catId, setCatId] = useState<number | null>(null);
  const [scId, setScId] = useState<number | null>(null);
  const [typeId, setTypeId] = useState<number | null>(null);

  const { data: categories, isLoading: lc } = useCatalogCategories(false);
  const { data: sousCategories, isLoading: lsc } = useCatalogSousCategories(catId, false, catId != null);
  const { data: types, isLoading: lt } = useCatalogTypes(scId, false, scId != null);

  const selectedCat = categories?.find((c) => c.id === catId);
  const selectedSc = sousCategories?.find((s) => s.id === scId);
  const selectedType = types?.find((t) => t.id === typeId);

  const productsQuery = useQuery<PaginatedResponse<Product>>({
    queryKey: ["catalog-sort-products", selectedCat?.name, selectedSc?.name, selectedType?.name],
    enabled: Boolean(selectedCat && selectedSc),
    queryFn: () => {
      const q = new URLSearchParams({ page: "1", page_size: "100" });
      q.set("categorie", selectedCat!.name);
      q.set("sous_categorie", selectedSc!.name);
      if (selectedType?.name) q.set("type_produit", selectedType.name);
      return productsApi.list(q).then((r) => r.data);
    },
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["catalog"] });
    qc.invalidateQueries({ queryKey: ["catalog-sort-products"] });
    qc.invalidateQueries({ queryKey: ["products"] });
  };

  const saveCats = useMutation({
    mutationFn: (ids: number[]) => catalogApi.reorderCategories(ids),
    onSuccess: () => { toast.success("Ordre des catégories enregistré"); invalidate(); },
    onError: (e) => toast.error(getErrorMessage(e, "Impossible d'enregistrer l'ordre")),
  });
  const saveSous = useMutation({
    mutationFn: (ids: number[]) => catalogApi.reorderSousCategories(catId!, ids),
    onSuccess: () => { toast.success("Ordre des sous-catégories enregistré"); invalidate(); },
    onError: (e) => toast.error(getErrorMessage(e, "Impossible d'enregistrer l'ordre")),
  });
  const saveTypes = useMutation({
    mutationFn: (ids: number[]) => catalogApi.reorderTypes(scId!, ids),
    onSuccess: () => { toast.success("Ordre des types enregistré"); invalidate(); },
    onError: (e) => toast.error(getErrorMessage(e, "Impossible d'enregistrer l'ordre")),
  });
  const saveProducts = useMutation({
    mutationFn: (ids: number[]) => catalogApi.reorderProducts(ids),
    onSuccess: () => { toast.success("Ordre des produits enregistré"); invalidate(); },
    onError: (e) => toast.error(getErrorMessage(e, "Impossible d'enregistrer l'ordre")),
  });

  const catRows: SortRow[] = useMemo(
    () => (categories ?? []).map((c) => ({ id: c.id, title: c.name })),
    [categories],
  );
  const scRows: SortRow[] = useMemo(
    () => (sousCategories ?? []).map((s) => ({ id: s.id, title: s.name })),
    [sousCategories],
  );
  const typeRows: SortRow[] = useMemo(
    () => (types ?? []).map((t) => ({
      id: t.id,
      title: t.name,
      subtitle: `${t.product_count ?? 0} produit(s)`,
    })),
    [types],
  );
  const productRows: SortRow[] = useMemo(
    () => (productsQuery.data?.items ?? []).map((p) => ({
      id: p.id,
      title: p.name,
      subtitle: p.product_code,
    })),
    [productsQuery.data],
  );

  if (lc) return <PageLoader />;

  return (
    <div className="page-content max-w-[1400px] space-y-6">
      <PageHeader
        title="Ordre du catalogue"
        subtitle={
          staffPageScope("catalogSort", role)
          ?? "Glissez-déposez pour définir l'ordre d'affichage (catégories → sous-catégories → types → produits)."
        }
        actions={
          <Link to="/catalog" className="btn-secondary">
            <Layers size={16} />
            Référentiels
          </Link>
        }
      />
      {role && (role === "admin" || role === "gestionnaire") && (
        <StaffScopeBanner page="catalogSort" role={role} />
      )}

      <p className="text-sm text-madec-muted">
        Sélectionnez une catégorie pour trier ses sous-catégories, puis une sous-catégorie pour trier les types et les produits.
        L'ordre est utilisé par l'API (y compris mobile).
      </p>

      <div className="grid gap-4 xl:grid-cols-4 md:grid-cols-2">
        <SortColumn
          title="Catégories"
          hint="Ordre global"
          rows={catRows}
          selectedId={catId}
          onSelect={(id) => { setCatId(id); setScId(null); setTypeId(null); }}
          onReorder={(ids) => saveCats.mutate(ids)}
          saving={saveCats.isPending}
        />
        <SortColumn
          title="Sous-catégories"
          hint={selectedCat ? selectedCat.name : "Sélectionnez une catégorie"}
          rows={scRows}
          selectedId={scId}
          disabled={!catId}
          loading={Boolean(catId) && lsc}
          onSelect={(id) => { setScId(id); setTypeId(null); }}
          onReorder={(ids) => saveSous.mutate(ids)}
          saving={saveSous.isPending}
        />
        <SortColumn
          title="Types"
          hint={selectedSc ? selectedSc.name : "Sélectionnez une sous-catégorie"}
          rows={typeRows}
          selectedId={typeId}
          disabled={!scId}
          loading={Boolean(scId) && lt}
          onSelect={setTypeId}
          onReorder={(ids) => saveTypes.mutate(ids)}
          saving={saveTypes.isPending}
        />
        <SortColumn
          title="Produits"
          hint={
            selectedType
              ? selectedType.name
              : selectedSc
                ? "Tous les produits de la sous-catégorie"
                : "Sélectionnez une sous-catégorie"
          }
          rows={productRows}
          disabled={!scId}
          loading={Boolean(scId && selectedSc) && productsQuery.isLoading}
          onReorder={(ids) => saveProducts.mutate(ids)}
          saving={saveProducts.isPending}
        />
      </div>
    </div>
  );
}

function SortColumn({
  title,
  hint,
  rows,
  selectedId,
  onSelect,
  onReorder,
  disabled,
  loading,
  saving,
}: {
  title: string;
  hint?: string;
  rows: SortRow[];
  selectedId?: number | null;
  onSelect?: (id: number) => void;
  onReorder: (ids: number[]) => void;
  disabled?: boolean;
  loading?: boolean;
  saving?: boolean;
}) {
  const [dragId, setDragId] = useState<number | null>(null);

  const move = (fromId: number, toId: number) => {
    if (fromId === toId) return;
    const ids = rows.map((r) => r.id);
    const from = ids.indexOf(fromId);
    const to = ids.indexOf(toId);
    if (from < 0 || to < 0) return;
    ids.splice(from, 1);
    ids.splice(to, 0, fromId);
    onReorder(ids);
  };

  const nudge = (id: number, dir: -1 | 1) => {
    const ids = rows.map((r) => r.id);
    const i = ids.indexOf(id);
    const j = i + dir;
    if (i < 0 || j < 0 || j >= ids.length) return;
    [ids[i], ids[j]] = [ids[j], ids[i]];
    onReorder(ids);
  };

  return (
    <div className={`card flex min-h-[28rem] flex-col space-y-3 ${disabled ? "opacity-60" : ""}`}>
      <div>
        <h2 className="text-sm font-semibold text-madec-text">{title}</h2>
        {hint && <p className="text-xs text-madec-muted">{hint}</p>}
      </div>
      {loading ? (
        <p className="text-sm text-madec-muted">Chargement…</p>
      ) : (
        <ul className="flex-1 space-y-1 overflow-y-auto">
          {rows.map((row, index) => (
            <li
              key={row.id}
              draggable={!disabled && rows.length > 1}
              onDragStart={() => setDragId(row.id)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (dragId != null) move(dragId, row.id);
                setDragId(null);
              }}
              onDragEnd={() => setDragId(null)}
              className={`flex items-center gap-1 rounded-lg px-1.5 py-1.5 text-sm ${
                selectedId === row.id ? "bg-madec-active ring-1 ring-madec-tint" : "hover:bg-madec-surface"
              } ${dragId === row.id ? "opacity-40" : ""}`}
            >
              <span className="cursor-grab text-madec-muted" title="Glisser pour trier">
                <GripVertical size={16} />
              </span>
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => onSelect?.(row.id)}
                disabled={!onSelect}
              >
                <span className="block truncate font-medium">{row.title}</span>
                {row.subtitle && (
                  <span className="block truncate text-[11px] text-madec-muted">{row.subtitle}</span>
                )}
              </button>
              <div className="flex shrink-0 flex-col">
                <button
                  type="button"
                  className="p-0.5 text-madec-muted hover:text-madec-primary disabled:opacity-30"
                  disabled={disabled || saving || index === 0}
                  onClick={() => nudge(row.id, -1)}
                  title="Monter"
                >
                  <ArrowUp size={12} />
                </button>
                <button
                  type="button"
                  className="p-0.5 text-madec-muted hover:text-madec-primary disabled:opacity-30"
                  disabled={disabled || saving || index === rows.length - 1}
                  onClick={() => nudge(row.id, 1)}
                  title="Descendre"
                >
                  <ArrowDown size={12} />
                </button>
              </div>
            </li>
          ))}
          {rows.length === 0 && (
            <li className="py-8 text-center text-sm text-madec-muted">
              {disabled ? "Sélection requise" : "Aucune entrée"}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
