import { useQuery } from "@tanstack/react-query";
import { catalogApi } from "../lib/api/services";
import type { CatalogCategorie, CatalogCategorieTreeNode, CatalogFamille, CatalogGamme, CatalogSousCategorie, CatalogSousFamille, CatalogType, OrgAgence, OrgSociete, OrgVille } from "../lib/types";

const CATALOG_STALE = 5 * 60_000;

export function useCatalogGammes(includeInactive = false, enabled = true) {
  return useQuery<CatalogGamme[]>({
    queryKey: ["catalog", "gammes", includeInactive],
    queryFn: () => catalogApi.gammes(includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogFamilles(gammeId?: number | null, includeInactive = false, enabled = true) {
  return useQuery<CatalogFamille[]>({
    queryKey: ["catalog", "familles", gammeId ?? "all", includeInactive],
    queryFn: () => catalogApi.familles(gammeId ?? undefined, includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogSousFamilles(familleId?: number | null, includeInactive = false, enabled = true) {
  return useQuery<CatalogSousFamille[]>({
    queryKey: ["catalog", "sous-familles", familleId ?? "all", includeInactive],
    queryFn: () => catalogApi.sousFamilles(familleId ?? undefined, includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogCategories(includeInactive = false, enabled = true) {
  return useQuery<CatalogCategorie[]>({
    queryKey: ["catalog", "categories", includeInactive],
    queryFn: () => catalogApi.categories(includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogSousCategories(categorieId?: number | null, includeInactive = false, enabled = true) {
  return useQuery<CatalogSousCategorie[]>({
    queryKey: ["catalog", "sous-categories", categorieId ?? "all", includeInactive],
    queryFn: () => catalogApi.sousCategories(categorieId ?? undefined, includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogCategoriesTree(includeInactive = false, enabled = true) {
  return useQuery<CatalogCategorieTreeNode[]>({
    queryKey: ["catalog", "categories-tree", includeInactive],
    queryFn: () => catalogApi.categoriesTree(includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogTypes(sousCategorieId?: number | null, includeInactive = false, enabled = true) {
  return useQuery<CatalogType[]>({
    queryKey: ["catalog", "types", sousCategorieId ?? "all", includeInactive],
    queryFn: () => catalogApi.types(sousCategorieId ?? undefined, includeInactive).then((r) => r.data),
    enabled: enabled && sousCategorieId != null,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogSocietes(includeInactive = false, enabled = true) {
  return useQuery<OrgSociete[]>({
    queryKey: ["catalog", "societes", includeInactive],
    queryFn: () => catalogApi.societes(includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogAgences(societeId?: number | null, includeInactive = false, enabled = true) {
  return useQuery<OrgAgence[]>({
    queryKey: ["catalog", "agences", societeId ?? "all", includeInactive],
    queryFn: () => catalogApi.agences(societeId ?? undefined, includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

export function useCatalogVilles(includeInactive = false, enabled = true) {
  return useQuery<OrgVille[]>({
    queryKey: ["catalog", "villes", includeInactive],
    queryFn: () => catalogApi.villes(includeInactive).then((r) => r.data),
    enabled,
    staleTime: CATALOG_STALE,
  });
}

/** Resolve gamme name → id for cascading filters. */
export function findGammeId(gammes: CatalogGamme[] | undefined, name: string) {
  if (!name || !gammes) return null;
  return gammes.find((g) => g.name.toLowerCase() === name.trim().toLowerCase())?.id ?? null;
}

export function findFamilleId(familles: CatalogFamille[] | undefined, name: string) {
  if (!name || !familles) return null;
  return familles.find((f) => f.name.toLowerCase() === name.trim().toLowerCase())?.id ?? null;
}

export function findSousCategorieId(
  sousCategories: { id: number; name: string }[] | undefined,
  name: string,
) {
  if (!name || !sousCategories?.length) return null;
  return sousCategories.find((s) => s.name === name)?.id ?? null;
}

export function findCategorieId(categories: CatalogCategorie[] | undefined, name: string) {
  if (!name || !categories) return null;
  return categories.find((c) => c.name.toLowerCase() === name.trim().toLowerCase())?.id ?? null;
}

export function findSocieteId(societes: OrgSociete[] | undefined, code: string) {
  if (!code || !societes) return null;
  return societes.find((s) => s.code.toLowerCase() === code.trim().toLowerCase())?.id ?? null;
}
