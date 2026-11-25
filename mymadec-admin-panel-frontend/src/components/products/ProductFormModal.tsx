import { useEffect } from "react";
import { useForm, useWatch, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import api from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";
import type { Product } from "../../lib/types";
import { Modal } from "../ui/Modal";
import { ComboSelect } from "../ui/ComboSelect";
import { CatalogSelect } from "../ui/CatalogSelect";
import {
  findCategorieId,
  findFamilleId,
  findGammeId,
  useCatalogCategories,
  useCatalogFamilles,
  useCatalogGammes,
  useCatalogSocietes,
  useCatalogSousCategories,
  useCatalogSousFamilles,
  useCatalogTypes,
  findSousCategorieId,
} from "../../hooks/useCatalog";
import {
  emptyProductForm,
  productSchema,
  productToForm,
  toProductPayload,
  type ProductForm,
} from "./productForm";

export function ProductFormModal({
  open,
  onClose,
  product,
}: {
  open: boolean;
  onClose: () => void;
  product?: Product | null;
}) {
  const qc = useQueryClient();
  const isEdit = !!product;

  const { register, handleSubmit, reset, control, setValue, formState: { errors } } = useForm<ProductForm>({
    resolver: zodResolver(productSchema),
    defaultValues: emptyProductForm(),
  });

  const gammeVal = useWatch({ control, name: "gamme" }) ?? "";
  const familleVal = useWatch({ control, name: "famille" }) ?? "";
  const categorieVal = useWatch({ control, name: "categorie" }) ?? "";
  const sousCategorieVal = useWatch({ control, name: "sous_categorie" }) ?? "";
  const { data: catalogGammes } = useCatalogGammes();
  const gammeId = findGammeId(catalogGammes, gammeVal);
  const { data: catalogFamilles } = useCatalogFamilles(gammeId);
  const familleId = findFamilleId(catalogFamilles, familleVal);
  const { data: catalogSousFamilles } = useCatalogSousFamilles(familleId);
  const { data: catalogCategories } = useCatalogCategories();
  const categorieId = findCategorieId(catalogCategories, categorieVal);
  const { data: catalogSousCategories } = useCatalogSousCategories(categorieId);
  const sousCategorieId = findSousCategorieId(catalogSousCategories, sousCategorieVal);
  const { data: catalogTypes } = useCatalogTypes(sousCategorieId);
  const { data: catalogSocietes } = useCatalogSocietes();

  const gammeOptions = catalogGammes?.map((g) => g.name) ?? [];
  const familleOptions = catalogFamilles?.map((f) => f.name) ?? [];
  const sousFamilleOptions = catalogSousFamilles?.map((s) => s.name) ?? [];
  const categorieOptions = catalogCategories?.map((c) => c.name) ?? [];
  const sousCategorieOptions = catalogSousCategories?.map((s) => s.name) ?? [];
  const typeOptions = catalogTypes?.map((t) => t.name) ?? [];
  const societeOptions = catalogSocietes?.map((s) => s.code) ?? [];

  useEffect(() => {
    if (!open) return;
    reset(product ? productToForm(product) : emptyProductForm());
  }, [open, product, reset]);

  useEffect(() => {
    if (!categorieVal || !sousCategorieVal) return;
    if (!sousCategorieOptions.includes(sousCategorieVal)) {
      setValue("sous_categorie", "");
    }
  }, [categorieVal, sousCategorieOptions, sousCategorieVal, setValue]);

  const save = useMutation({
    mutationFn: (d: ProductForm) =>
      isEdit
        ? api.put(`/products/${product!.id}`, toProductPayload(d, true))
        : api.post("/products", toProductPayload(d, false)),
    onSuccess: () => {
      toast.success(isEdit ? "Produit mis à jour" : "Produit créé");
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["catalog"] });
      qc.invalidateQueries({ queryKey: ["categories"] });
      qc.invalidateQueries({ queryKey: ["sous-categories"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      if (product?.id) {
        qc.invalidateQueries({ queryKey: ["product", product.id] });
      }
      reset();
      onClose();
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Modifier le produit" : "Nouveau produit"} size={isEdit ? "md" : "lg"}>
      <form onSubmit={handleSubmit((d) => save.mutate(d))} className="space-y-3">
        {isEdit ? (
          <>
            <div className="rounded-lg border border-madec-border bg-madec-surface px-3 py-2 text-sm">
              <p className="font-mono text-xs text-madec-muted">{product!.product_code}</p>
            </div>
            <div>
              <label className="label">Désignation *</label>
              <input {...register("name")} className="input" />
              {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
            </div>
            <div>
              <label className="label">Description</label>
              <textarea {...register("description")} className="input" rows={3} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Marque (gamme) *</label>
                <Controller name="gamme" control={control} render={({ field }) => (
                  <CatalogSelect id="pf-marque" value={field.value ?? ""} onChange={field.onChange} options={gammeOptions} placeholder="Choisir une marque" />
                )} />
                {errors.gamme && <p className="text-xs text-red-500">{errors.gamme.message}</p>}
              </div>
              <div>
                <label className="label">Type *</label>
                <Controller name="type_produit" control={control} render={({ field }) => (
                  <CatalogSelect
                    id="pf-type"
                    value={field.value ?? ""}
                    onChange={field.onChange}
                    options={typeOptions.length ? typeOptions : (field.value ? [field.value] : [])}
                    placeholder={sousCategorieVal ? "Choisir un type" : "Choisir sous-catégorie d’abord"}
                    disabled={!sousCategorieVal}
                  />
                )} />
                {errors.type_produit && <p className="text-xs text-red-500">{errors.type_produit.message}</p>}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Catégorie</label>
                <Controller name="categorie" control={control} render={({ field }) => (
                  <CatalogSelect id="pf-categorie" value={field.value ?? ""} onChange={(v) => { field.onChange(v); setValue("sous_categorie", ""); setValue("type_produit", ""); }} options={categorieOptions} placeholder="Choisir une catégorie" />
                )} />
              </div>
              <div>
                <label className="label">Sous-catégorie</label>
                <Controller name="sous_categorie" control={control} render={({ field }) => (
                  <CatalogSelect id="pf-sous-categorie" value={field.value ?? ""} onChange={(v) => { field.onChange(v); setValue("type_produit", ""); }} options={sousCategorieOptions} placeholder="Choisir une sous-catégorie" disabled={!categorieVal} />
                )} />
              </div>
            </div>
            <div>
              <label className="label">Promotion (%)</label>
              <input
                {...register("discount_rate", { setValueAs: (v) => (v === "" || v == null ? 0 : Number(v)) })}
                type="number"
                step="0.1"
                min="0"
                max="100"
                readOnly
                tabIndex={-1}
                aria-readonly="true"
                className="input cursor-not-allowed bg-madec-surface text-madec-muted"
              />
              <p className="mt-0.5 text-[10px] text-madec-muted">Lecture seule · géré par l’ERP / Sync</p>
            </div>
            <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-madec-border px-3 py-2">
              <Controller
                name="is_liquidation"
                control={control}
                render={({ field }) => (
                  <input
                    type="checkbox"
                    checked={!!field.value}
                    onChange={(e) => field.onChange(e.target.checked)}
                    className="mt-0.5 rounded border-madec-border text-madec-primary"
                  />
                )}
              />
              <span className="text-sm">
                <span className="font-medium text-madec-text">Liquidation</span>
                <span className="mt-0.5 block text-[10px] text-madec-muted">
                  Si coché, le produit apparaît dans les Liquidations (app mobile et page Promptinos)
                </span>
              </span>
            </label>
          </>
        ) : (
          <>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Code produit *</label>
            <input {...register("product_code")} className="input" />
            {errors.product_code && <p className="text-xs text-red-500">{errors.product_code.message}</p>}
          </div>
          <div>
            <label className="label">Désignation *</label>
            <input {...register("name")} className="input" />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>
        </div>
        <div>
          <label className="label">Description</label>
          <textarea {...register("description")} className="input" rows={2} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="label">Marque (gamme) *</label>
            <Controller name="gamme" control={control} render={({ field }) => (
              <ComboSelect id="pf-gamme" value={field.value ?? ""} onChange={(v) => { field.onChange(v); setValue("famille", ""); setValue("sous_famille", ""); }} options={gammeOptions} placeholder="Choisir ou saisir" />
            )} />
            {errors.gamme && <p className="text-xs text-red-500">{errors.gamme.message}</p>}
          </div>
          <div>
            <label className="label">Famille</label>
            <Controller name="famille" control={control} render={({ field }) => (
              <ComboSelect id="pf-famille" value={field.value ?? ""} onChange={(v) => { field.onChange(v); setValue("sous_famille", ""); }} options={familleOptions} placeholder="Choisir ou saisir" />
            )} />
            <p className="mt-0.5 text-[10px] text-madec-muted">Sync / ERP</p>
          </div>
          <div>
            <label className="label">Sous-famille</label>
            <Controller name="sous_famille" control={control} render={({ field }) => (
              <ComboSelect id="pf-sous-famille" value={field.value ?? ""} onChange={field.onChange} options={sousFamilleOptions} placeholder="Choisir ou saisir" />
            )} />
            <p className="mt-0.5 text-[10px] text-madec-muted">Sync / ERP</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Catégorie</label>
            <Controller name="categorie" control={control} render={({ field }) => (
              <CatalogSelect id="pf-categorie-new" value={field.value ?? ""} onChange={(v) => { field.onChange(v); setValue("sous_categorie", ""); }} options={categorieOptions} placeholder="Choisir une catégorie" />
            )} />
            <p className="mt-0.5 text-[10px] text-madec-muted">App mobile — gérer dans Référentiels</p>
          </div>
          <div>
            <label className="label">Sous-catégorie</label>
            <Controller name="sous_categorie" control={control} render={({ field }) => (
              <CatalogSelect id="pf-sous-categorie-new" value={field.value ?? ""} onChange={field.onChange} options={sousCategorieOptions} placeholder="Choisir une sous-catégorie" disabled={!categorieVal} />
            )} />
            <p className="mt-0.5 text-[10px] text-madec-muted">App mobile</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div><label className="label">Unité</label><input {...register("unit")} className="input" /></div>
          <div><label className="label">PSG Code</label><input {...register("productsalesgroup_code")} className="input" /></div>
          <div>
            <label className="label">Société</label>
            <Controller name="society_code" control={control} render={({ field }) => (
              <ComboSelect id="pf-societe" value={field.value ?? ""} onChange={field.onChange} options={societeOptions} placeholder="Code société" />
            )} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Prix de base (MAD)</label>
            <input {...register("base_price", { setValueAs: (v) => (v === "" || v == null ? null : Number(v)) })} type="number" step="0.01" min="0" className="input" />
          </div>
          <div>
            <label className="label">Remise (%)</label>
            <input {...register("discount_rate", { setValueAs: (v) => (v === "" || v == null ? 0 : Number(v)) })} type="number" step="0.1" min="0" max="100" className="input" />
          </div>
        </div>
          </>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">Annuler</button>
          <button type="submit" disabled={save.isPending} className="btn-primary">
            {save.isPending ? "..." : isEdit ? "Enregistrer" : "Créer"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
