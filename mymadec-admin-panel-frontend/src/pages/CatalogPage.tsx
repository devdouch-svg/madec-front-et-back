import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Database, ImageIcon, Pencil, ToggleLeft, ToggleRight, Upload, X } from "lucide-react";
import toast from "react-hot-toast";
import { PageHeader } from "../components/layout/PageHeader";
import { useRole } from "../lib/roles";
import { staffCan, staffPageScope } from "../lib/staffCapabilities";
import { StaffScopeBanner } from "../components/staff/StaffScopeBanner";
import { PageLoader } from "../components/ui/Spinner";
import { catalogApi } from "../lib/api/services";
import { getErrorMessage } from "../lib/errors";
import { mediaUrl } from "../lib/media";
import {
  useCatalogAgences,
  useCatalogCategories,
  useCatalogCategoriesTree,
  useCatalogFamilles,
  useCatalogGammes,
  useCatalogSocietes,
  useCatalogSousCategories,
  useCatalogSousFamilles,
  useCatalogTypes,
  useCatalogVilles,
} from "../hooks/useCatalog";

type Tab = "catalogue" | "organisation";

export function CatalogPage() {
  const [tab, setTab] = useState<Tab>("catalogue");
  const qc = useQueryClient();
  const { isAdmin, role } = useRole();

  const { data: gammes, isLoading: lg } = useCatalogGammes(true);
  const [selectedGammeId, setSelectedGammeId] = useState<number | null>(null);
  const { data: familles, isLoading: lf } = useCatalogFamilles(selectedGammeId, true);
  const [selectedFamilleId, setSelectedFamilleId] = useState<number | null>(null);
  const { data: sousFamilles, isLoading: lsf } = useCatalogSousFamilles(selectedFamilleId, true);

  const { data: categories, isLoading: lc } = useCatalogCategories(true);
  const { data: mobileTree } = useCatalogCategoriesTree(true);
  const [selectedCategorieId, setSelectedCategorieId] = useState<number | null>(null);
  const [selectedSousCategorieId, setSelectedSousCategorieId] = useState<number | null>(null);
  const { data: sousCategories, isLoading: lsc } = useCatalogSousCategories(selectedCategorieId, true);
  const { data: catalogTypes, isLoading: lt } = useCatalogTypes(selectedSousCategorieId, true);

  const mobileCatCounts = useMemo(() => {
    const m = new Map<number, number>();
    mobileTree?.forEach((c) => m.set(c.id, c.product_count));
    return m;
  }, [mobileTree]);

  const mobileScCounts = useMemo(() => {
    const m = new Map<number, number>();
    mobileTree?.forEach((c) => c.sous_categories.forEach((sc) => m.set(sc.id, sc.product_count)));
    return m;
  }, [mobileTree]);

  const mobileTypeCounts = useMemo(() => {
    const m = new Map<number, number>();
    mobileTree?.forEach((c) =>
      c.sous_categories.forEach((sc) =>
        (sc.types ?? []).forEach((tp) => m.set(tp.id, tp.product_count)),
      ),
    );
    return m;
  }, [mobileTree]);

  const { data: societes, isLoading: ls } = useCatalogSocietes(true);
  const [selectedSocieteId, setSelectedSocieteId] = useState<number | null>(null);
  const { data: agences, isLoading: la } = useCatalogAgences(selectedSocieteId, true);
  const { data: villes, isLoading: lv } = useCatalogVilles(true);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["catalog"] });

  const importData = useMutation({
    mutationFn: () => catalogApi.importFromData(),
    onSuccess: (r) => {
      const d = r.data;
      toast.success(
        `Import terminé — ${d.gammes} gammes, ${d.categories} catégories, ${d.societes} sociétés`,
      );
      invalidate();
    },
    onError: (e) => toast.error(getErrorMessage(e, "Import impossible")),
  });

  const uploadCategorieImage = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) => catalogApi.uploadCategorieImage(id, file),
    onSuccess: () => {
      toast.success("Image catégorie mise à jour");
      invalidate();
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur upload")),
  });

  if (lg || ls || lv || lc) return <PageLoader />;

  return (
    <div className="page-content max-w-7xl space-y-6">
      <PageHeader
        title="Référentiels"
        subtitle={staffPageScope("catalog", role) ?? "Gammes, catégories mobile, sociétés, agences et villes"}
        actions={
          <>
            <Link to="/catalog/order" className="btn-secondary">
              Trier le catalogue
            </Link>
            {staffCan("import_catalog", role) ? (
              <button
                type="button"
                className="btn-secondary"
                disabled={importData.isPending}
                onClick={() => importData.mutate()}
              >
                <Database size={16} />
                Importer depuis les données existantes
              </button>
            ) : null}
          </>
        }
      />

      {role && (role === "admin" || role === "gestionnaire") && (
        <StaffScopeBanner page="catalog" role={role} />
      )}

      {!isAdmin && (
        <p className="text-xs text-madec-muted -mt-4">
          L&apos;import global des référentiels est réservé à l&apos;administrateur.
        </p>
      )}

      <div className="flex gap-2 border-b border-madec-border pb-1">
        {(["catalogue", "organisation"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded-lg px-4 py-2 text-sm font-medium capitalize ${
              tab === t ? "bg-madec-active text-madec-primary" : "text-madec-secondary hover:bg-madec-surface"
            }`}
          >
            {t === "catalogue" ? "Catalogue produits" : "Organisation"}
          </button>
        ))}
      </div>

      {tab === "catalogue" && (
        <div className="space-y-8">
          <section className="space-y-3">
            <div>
              <h2 className="text-sm font-semibold text-madec-text">Synchronisation (serveur intermédiaire)</h2>
              <p className="text-xs text-madec-muted">Gamme, famille et sous-famille — alignées avec l&apos;ERP et l&apos;ETL.</p>
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <RefPanel
                title="Gammes"
                loading={lg}
                rows={gammes?.map((g) => ({ id: g.id, primary: g.name, active: g.is_active })) ?? []}
                selectedId={selectedGammeId}
                onSelect={(id) => { setSelectedGammeId(id); setSelectedFamilleId(null); }}
                onToggle={async (id, active) => { await catalogApi.updateGamme(id, { is_active: active }); invalidate(); }}
              />
              <RefPanel
                title="Familles"
                loading={lf}
                disabled={!selectedGammeId}
                hint={selectedGammeId ? undefined : "Sélectionnez une gamme"}
                rows={familles?.map((f) => ({ id: f.id, primary: f.name, active: f.is_active })) ?? []}
                selectedId={selectedFamilleId}
                onSelect={setSelectedFamilleId}
                onToggle={async (id, active) => { await catalogApi.updateFamille(id, { is_active: active }); invalidate(); }}
              />
              <RefPanel
                title="Sous-familles"
                loading={lsf}
                disabled={!selectedFamilleId}
                hint={selectedFamilleId ? undefined : "Sélectionnez une famille"}
                rows={sousFamilles?.map((s) => ({ id: s.id, primary: s.name, active: s.is_active })) ?? []}
                onToggle={async (id, active) => { await catalogApi.updateSousFamille(id, { is_active: active }); invalidate(); }}
              />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex flex-wrap items-end justify-between gap-2">
              <div>
                <h2 className="text-sm font-semibold text-madec-text">Application mobile</h2>
                <p className="text-xs text-madec-muted">
                  Catégorie → sous-catégorie → type — navigation mobile et liste déroulante produit.
                </p>
              </div>
              <Link
                to="/products?missing_mobile_category=true"
                className="text-xs font-medium text-madec-primary hover:text-madec-primary"
              >
                Voir produits sans catégorie →
              </Link>
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <RefPanel
                title="Catégories"
                loading={lc}
                rows={categories?.map((c) => ({
                  id: c.id,
                  primary: c.name,
                  secondary: `${mobileCatCounts.get(c.id) ?? 0} produit(s)`,
                  active: c.is_active,
                  image_path: c.image_path,
                  updated_at: c.updated_at,
                })) ?? []}
                selectedId={selectedCategorieId}
                onSelect={(id) => {
                  setSelectedCategorieId(id);
                  setSelectedSousCategorieId(null);
                }}
                onAdd={async (name) => { await catalogApi.createCategorie(name); invalidate(); }}
                onRename={async (id, name) => { await catalogApi.updateCategorie(id, { name }); invalidate(); }}
                onToggle={async (id, active) => { await catalogApi.updateCategorie(id, { is_active: active }); invalidate(); }}
                onUploadImage={async (id, file) => {
                  await uploadCategorieImage.mutateAsync({ id, file });
                }}
              />
              <RefPanel
                title="Sous-catégories"
                loading={lsc}
                disabled={!selectedCategorieId}
                hint={selectedCategorieId ? undefined : "Sélectionnez une catégorie"}
                rows={sousCategories?.map((s) => ({
                  id: s.id,
                  primary: s.name,
                  secondary: `${mobileScCounts.get(s.id) ?? 0} produit(s)`,
                  active: s.is_active,
                })) ?? []}
                selectedId={selectedSousCategorieId}
                onSelect={setSelectedSousCategorieId}
                onAdd={async (name) => {
                  if (!selectedCategorieId) return;
                  await catalogApi.createSousCategorie(selectedCategorieId, name);
                  invalidate();
                }}
                onRename={async (id, name) => { await catalogApi.updateSousCategorie(id, { name }); invalidate(); }}
                onToggle={async (id, active) => { await catalogApi.updateSousCategorie(id, { is_active: active }); invalidate(); }}
              />
              <RefPanel
                title="Types"
                loading={lt}
                disabled={!selectedSousCategorieId}
                hint={selectedSousCategorieId ? undefined : "Sélectionnez une sous-catégorie"}
                rows={catalogTypes?.map((t) => ({
                  id: t.id,
                  primary: t.name,
                  secondary: `${mobileTypeCounts.get(t.id) ?? t.product_count ?? 0} produit(s)`,
                  active: t.is_active,
                })) ?? []}
                onAdd={async (name) => {
                  if (!selectedSousCategorieId) return;
                  await catalogApi.createType(selectedSousCategorieId, name);
                  invalidate();
                }}
                onRename={async (id, name) => { await catalogApi.updateType(id, { name }); invalidate(); }}
                onToggle={async (id, active) => { await catalogApi.updateType(id, { is_active: active }); invalidate(); }}
              />
            </div>
          </section>
        </div>
      )}

      {tab === "organisation" && (
        <div className="grid gap-4 lg:grid-cols-3">
          <RefPanel
            title="Sociétés"
            loading={ls}
            rows={societes?.map((s) => ({ id: s.id, primary: s.code, secondary: s.label, active: s.is_active })) ?? []}
            selectedId={selectedSocieteId}
            onSelect={setSelectedSocieteId}
            onToggle={async (id, active) => { await catalogApi.updateSociete(id, { is_active: active }); invalidate(); }}
          />
          <RefPanel
            title="Agences"
            loading={la}
            disabled={!selectedSocieteId}
            hint={selectedSocieteId ? undefined : "Sélectionnez une société"}
            rows={agences?.map((a) => ({ id: a.id, primary: a.code, secondary: a.label, active: a.is_active })) ?? []}
            onToggle={async (id, active) => { await catalogApi.updateAgence(id, { is_active: active }); invalidate(); }}
          />
          <RefPanel
            title="Villes"
            loading={lv}
            rows={villes?.map((v) => ({ id: v.id, primary: v.code, secondary: v.label, active: v.is_active })) ?? []}
            onToggle={async (id, active) => { await catalogApi.updateVille(id, { is_active: active }); invalidate(); }}
          />
        </div>
      )}
    </div>
  );
}

interface RefRow {
  id: number;
  primary: string;
  secondary?: string;
  active: boolean;
  image_path?: string | null;
  updated_at?: string;
}

function RefPanel({
  title,
  rows,
  loading,
  selectedId,
  onSelect,
  onAdd,
  onRename,
  onToggle,
  onUploadImage,
  disabled,
  hint,
  addLabel = "Nom",
}: {
  title: string;
  rows: RefRow[];
  loading?: boolean;
  selectedId?: number | null;
  onSelect?: (id: number) => void;
  onAdd?: (value: string) => Promise<void>;
  onRename?: (id: number, value: string) => Promise<void>;
  onToggle: (id: number, active: boolean) => Promise<void>;
  onUploadImage?: (id: number, file: File) => Promise<void>;
  disabled?: boolean;
  hint?: string;
  addLabel?: string;
}) {
  const [value, setValue] = useState("");
  const [pending, setPending] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [renamePending, setRenamePending] = useState(false);
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});

  const submit = async () => {
    const v = value.trim();
    if (!v || disabled || !onAdd) return;
    setPending(true);
    try {
      await onAdd(v);
      setValue("");
      toast.success(`${title} ajouté(e)`);
    } catch (e) {
      toast.error(getErrorMessage(e, "Erreur"));
    } finally {
      setPending(false);
    }
  };

  const startRename = (row: RefRow) => {
    setEditingId(row.id);
    setEditValue(row.primary);
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditValue("");
  };

  const saveRename = async () => {
    if (editingId == null || !onRename) return;
    const v = editValue.trim();
    if (!v) {
      toast.error("Le nom est requis");
      return;
    }
    const current = rows.find((r) => r.id === editingId)?.primary?.trim();
    if (current && current.toLowerCase() === v.toLowerCase()) {
      cancelRename();
      return;
    }
    setRenamePending(true);
    try {
      await onRename(editingId, v);
      toast.success("Nom modifié");
      cancelRename();
    } catch (e) {
      toast.error(getErrorMessage(e, "Erreur"));
    } finally {
      setRenamePending(false);
    }
  };

  return (
    <div className="card space-y-3">
      <h2 className="text-sm font-semibold text-madec-text">{title}</h2>
      {hint && <p className="text-xs text-madec-muted">{hint}</p>}
      {onAdd && (
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder={addLabel}
            value={value}
            disabled={disabled || pending}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); submit(); } }}
          />
          <button type="button" className="btn-primary btn-sm" disabled={disabled || pending || !value.trim()} onClick={submit}>
            Ajouter
          </button>
        </div>
      )}
      {loading ? (
        <p className="text-sm text-madec-muted">Chargement…</p>
      ) : (
        <ul className="max-h-72 space-y-1 overflow-y-auto">
          {rows.map((row) => (
            <li
              key={row.id}
              className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm ${
                selectedId === row.id ? "bg-madec-active ring-1 ring-madec-tint" : "hover:bg-madec-surface"
              } ${!row.active ? "opacity-50" : ""}`}
            >
              {onUploadImage && (
                <div className="relative shrink-0">
                  {row.image_path ? (
                    <img
                      src={mediaUrl(row.image_path, row.updated_at)}
                      alt=""
                      className="h-10 w-10 rounded-md object-cover ring-1 ring-madec-border"
                    />
                  ) : (
                    <div className="flex h-10 w-10 items-center justify-center rounded-md bg-madec-tint text-madec-muted/50">
                      <ImageIcon size={16} />
                    </div>
                  )}
                  <button
                    type="button"
                    className="absolute -bottom-1 -right-1 rounded-full bg-white p-0.5 text-madec-muted shadow ring-1 ring-madec-border hover:text-madec-primary"
                    title="Changer l'image"
                    onClick={() => fileRefs.current[row.id]?.click()}
                  >
                    <Upload size={10} />
                  </button>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    ref={(el) => { fileRefs.current[row.id] = el; }}
                    onChange={async (e) => {
                      const f = e.target.files?.[0];
                      if (!f) return;
                      try {
                        await onUploadImage(row.id, f);
                      } catch (err) {
                        toast.error(getErrorMessage(err, "Erreur upload"));
                      } finally {
                        e.target.value = "";
                      }
                    }}
                  />
                </div>
              )}
              {editingId === row.id ? (
                <div className="flex min-w-0 flex-1 items-center gap-1">
                  <input
                    className="input flex-1 py-1 text-sm"
                    value={editValue}
                    disabled={renamePending}
                    autoFocus
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        void saveRename();
                      }
                      if (e.key === "Escape") {
                        e.preventDefault();
                        cancelRename();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="p-1 text-green-600 hover:text-green-700"
                    title="Enregistrer"
                    disabled={renamePending || !editValue.trim()}
                    onClick={() => void saveRename()}
                  >
                    <Check size={16} />
                  </button>
                  <button
                    type="button"
                    className="p-1 text-madec-muted hover:text-madec-text"
                    title="Annuler"
                    disabled={renamePending}
                    onClick={cancelRename}
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <>
                  <button
                    type="button"
                    className="min-w-0 flex-1 text-left"
                    onClick={() => onSelect?.(row.id)}
                    disabled={!onSelect}
                  >
                    <span className="font-medium">{row.primary}</span>
                    {row.secondary && row.secondary !== row.primary && (
                      <span className="ml-2 text-xs text-madec-muted">{row.secondary}</span>
                    )}
                  </button>
                  {onRename && (
                    <button
                      type="button"
                      className="p-1 text-madec-muted hover:text-madec-primary"
                      title="Modifier le nom"
                      onClick={() => startRename(row)}
                    >
                      <Pencil size={14} />
                    </button>
                  )}
                </>
              )}
              <button
                type="button"
                className="p-1 text-madec-muted hover:text-madec-primary"
                title={row.active ? "Désactiver" : "Activer"}
                onClick={async () => {
                  try {
                    await onToggle(row.id, !row.active);
                    toast.success(row.active ? "Désactivé" : "Activé");
                  } catch (e) {
                    toast.error(getErrorMessage(e, "Erreur"));
                  }
                }}
              >
                {row.active ? <ToggleRight size={16} className="text-green-500" /> : <ToggleLeft size={16} />}
              </button>
            </li>
          ))}
          {rows.length === 0 && <li className="text-sm text-madec-muted py-4 text-center">Aucune entrée</li>}
        </ul>
      )}
    </div>
  );
}
