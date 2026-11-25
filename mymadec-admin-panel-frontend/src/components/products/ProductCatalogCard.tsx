import {
  CheckSquare,
  Package,
  Pencil,
  ScanLine,
  ShoppingCart,
  Square,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Upload,
} from "lucide-react";
import type { Product } from "../../lib/types";
import { mediaUrl } from "../../lib/media";
import { ProductPrice } from "./ProductPrice";

interface ProductCatalogCardProps {
  product: Product;
  selectionMode?: boolean;
  selected?: boolean;
  isAdmin?: boolean;
  isAdminOrGest?: boolean;
  isAcheteur?: boolean;
  onToggleSelect?: () => void;
  onView: () => void;
  onEdit?: () => void;
  onAssign?: () => void;
  onToggleActive?: () => void;
  onAddToCart?: () => void;
  onUploadImage?: () => void;
  onDeleteImage?: () => void;
  fileInputRef?: (el: HTMLInputElement | null) => void;
  onFileChange?: (file: File) => void;
}

export function ProductCatalogCard({
  product,
  selectionMode,
  selected,
  isAdmin,
  isAdminOrGest,
  isAcheteur,
  onToggleSelect,
  onView,
  onEdit,
  onAssign,
  onToggleActive,
  onAddToCart,
  onUploadImage,
  onDeleteImage,
  fileInputRef,
  onFileChange,
}: ProductCatalogCardProps) {
  return (
    <article
      className={`product-card group flex flex-col overflow-hidden ${
        !product.is_active ? "opacity-60" : ""
      } ${selected ? "ring-2 ring-madec-primary" : ""}`}
    >
      <div className="relative">
        {selectionMode && isAdminOrGest && (
          <button
            type="button"
            className="absolute left-2 top-2 z-10 rounded-lg bg-white/95 p-1.5 shadow-sm ring-1 ring-madec-border"
            onClick={onToggleSelect}
          >
            {selected ? (
              <CheckSquare size={16} className="text-madec-primary" />
            ) : (
              <Square size={16} className="text-madec-muted" />
            )}
          </button>
        )}

        <button type="button" className="block w-full text-left" onClick={onView}>
          {product.image_path ? (
            <img
              src={mediaUrl(product.image_path, product.updated_at)}
              alt={product.name}
              className="product-card-image w-full object-contain transition-transform duration-300 group-hover:scale-[1.02]"
            />
          ) : (
            <div className="product-card-image flex w-full items-center justify-center text-madec-muted/50">
              <Package size={40} strokeWidth={1.25} />
            </div>
          )}
        </button>

        {product.discount_rate > 0 && (
          <span className="badge-promo absolute left-0 top-3">−{product.discount_rate}%</span>
        )}

        {!product.is_active && isAdminOrGest && (
          <span className="badge-tag absolute right-0 top-3">Inactif</span>
        )}

        {isAdminOrGest && (
          <div className="absolute right-2 top-2 flex gap-1">
            <button
              type="button"
              onClick={onUploadImage}
              className="btn-icon !rounded-lg bg-white/95 p-1.5 shadow-sm ring-1 ring-madec-border"
              title="Changer l'image"
            >
              <Upload size={13} />
            </button>
            {product.image_path && (
              <button
                type="button"
                onClick={onDeleteImage}
                className="btn-icon !rounded-lg bg-white/95 p-1.5 shadow-sm ring-1 ring-madec-border hover:!text-madec-danger"
                title="Supprimer l'image"
              >
                <Trash2 size={13} />
              </button>
            )}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              ref={fileInputRef}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onFileChange?.(f);
              }}
            />
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <p className="text-[10px] font-mono uppercase tracking-wide text-madec-muted">
          {product.product_code}
        </p>
        <button
          type="button"
          onClick={onView}
          className="mt-0.5 line-clamp-2 text-left text-sm font-semibold leading-snug text-madec-text transition-colors group-hover:text-madec-primary"
        >
          {product.name}
        </button>

        {product.categorie ? (
          <p className="mt-1.5 text-xs font-medium text-madec-primary">
            {product.categorie}
            {product.sous_categorie ? ` · ${product.sous_categorie}` : ""}
          </p>
        ) : isAdminOrGest ? (
          <span className="mt-1.5 inline-flex w-fit rounded bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 ring-1 ring-amber-200">
            Sans catégorie mobile
          </span>
        ) : null}

        {product.gamme && (
          <p className="mt-1 text-[10px] text-madec-muted">
            {product.gamme}
            {product.famille ? ` · ${product.famille}` : ""}
          </p>
        )}

        <div className="mt-auto pt-3">
          <div className="flex items-end justify-between gap-2">
            <ProductPrice
              basePrice={product.base_price}
              finalPrice={product.final_price}
              discountRate={product.discount_rate}
              unit={product.unit}
              size="sm"
            />

            {isAcheteur && (
              <button
                type="button"
                onClick={onAddToCart}
                className="product-card-cart-btn"
                disabled={!product.is_active}
                title="Ajouter au panier"
              >
                <ShoppingCart size={16} className="text-madec-primary" />
              </button>
            )}
          </div>

          {isAdminOrGest && (
            <div className="mt-3 flex items-center justify-end gap-0.5 border-t border-madec-border pt-2">
              <button
                type="button"
                title="Modifier"
                onClick={onEdit}
                className="btn-icon !p-1.5"
              >
                <Pencil size={15} />
              </button>
              <button
                type="button"
                title="Assigner catalogue"
                onClick={onAssign}
                className="btn-icon !p-1.5"
              >
                <ScanLine size={15} />
              </button>
              {isAdmin && (
                <button
                  type="button"
                  title={product.is_active ? "Désactiver" : "Activer"}
                  onClick={onToggleActive}
                  className="btn-icon !p-1.5"
                >
                  {product.is_active ? (
                    <ToggleRight size={17} className="text-madec-success" />
                  ) : (
                    <ToggleLeft size={17} />
                  )}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
