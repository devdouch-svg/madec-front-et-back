import { z } from "zod";
import type { Product } from "../../lib/types";

export const productSchema = z.object({
  product_code: z.string().trim().min(1, "Code produit requis"),
  name: z.string().trim().min(1, "Désignation requise"),
  description: z.string().optional(),
  unit: z.string().optional(),
  type_produit: z.string().trim().min(1, "Type requis"),
  gamme: z.string().trim().min(1, "Marque (gamme) requise"),
  famille: z.string().optional(),
  sous_famille: z.string().optional(),
  categorie: z.string().optional(),
  sous_categorie: z.string().optional(),
  productsalesgroup_code: z.string().optional(),
  society_code: z.string().optional(),
  base_price: z.number().nullable().optional(),
  discount_rate: z.number().optional(),
  is_liquidation: z.boolean().optional(),
});

export type ProductForm = z.infer<typeof productSchema>;

export function emptyProductForm(): ProductForm {
  return {
    product_code: "",
    name: "",
    description: "",
    unit: "",
    type_produit: "",
    gamme: "",
    famille: "",
    sous_famille: "",
    categorie: "",
    sous_categorie: "",
    productsalesgroup_code: "",
    society_code: "",
    base_price: null,
    discount_rate: 0,
    is_liquidation: false,
  };
}

export function productToForm(product: Product): ProductForm {
  return {
    product_code: product.product_code,
    name: product.name,
    description: product.description ?? "",
    unit: product.unit ?? "",
    type_produit: product.type_produit ?? "",
    gamme: product.gamme ?? "",
    famille: product.famille ?? "",
    sous_famille: product.sous_famille ?? "",
    categorie: product.categorie ?? "",
    sous_categorie: product.sous_categorie ?? "",
    productsalesgroup_code: product.productsalesgroup_code ?? "",
    society_code: product.society_code ?? "",
    base_price: product.base_price,
    discount_rate: product.discount_rate,
    is_liquidation: product.is_liquidation ?? false,
  };
}

export function toProductPayload(d: ProductForm, isEdit: boolean) {
  const opt = (v?: string | null) => {
    const trimmed = v?.trim();
    return trimmed ? trimmed : null;
  };
  if (isEdit) {
    const discount = d.discount_rate ?? 0;
    return {
      name: d.name.trim(),
      description: opt(d.description),
      type_produit: opt(d.type_produit),
      gamme: opt(d.gamme),
      categorie: opt(d.categorie),
      sous_categorie: opt(d.sous_categorie),
      discount_rate: discount,
      // Liquidation is independent of ERP discount_rate (often 0 / read-only).
      is_liquidation: d.is_liquidation ?? false,
    };
  }
  const payload = {
    name: d.name.trim(),
    description: opt(d.description),
    unit: opt(d.unit),
    type_produit: opt(d.type_produit),
    gamme: opt(d.gamme),
    famille: opt(d.famille),
    sous_famille: opt(d.sous_famille),
    categorie: opt(d.categorie),
    sous_categorie: opt(d.sous_categorie),
    productsalesgroup_code: opt(d.productsalesgroup_code),
    society_code: opt(d.society_code),
    base_price: d.base_price,
    discount_rate: d.discount_rate ?? 0,
  };
  return { product_code: d.product_code.trim(), ...payload };
}
