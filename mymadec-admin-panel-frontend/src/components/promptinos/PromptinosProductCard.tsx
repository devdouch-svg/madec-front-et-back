import { Package, ShoppingCart } from "lucide-react";
import type { Product } from "../../lib/types";
import { mediaUrl } from "../../lib/media";
import { ProductPrice } from "../products/ProductPrice";

interface PromptinosProductCardProps {
  product: Product;
  cartQty?: number;
  showCart?: boolean;
  showStaffBadge?: boolean;
  onView: (product: Product) => void;
  onAddToCart: (product: Product) => void;
}

export function PromptinosProductCard({
  product,
  cartQty = 0,
  showCart = false,
  showStaffBadge = false,
  onView,
  onAddToCart,
}: PromptinosProductCardProps) {
  return (
    <article
      className={`card-hover group flex !p-0 flex-col overflow-hidden ${
        !product.is_active ? "opacity-60" : ""
      }`}
    >
      <button
        type="button"
        className="relative block w-full text-left"
        onClick={() => onView(product)}
      >
        {product.image_path ? (
          <img
            src={mediaUrl(product.image_path, product.updated_at)}
            alt=""
            className="h-44 w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />
        ) : (
          <div className="flex h-44 items-center justify-center bg-gradient-to-br from-madec-surface to-madec-tint text-madec-muted/50">
            <Package size={40} strokeWidth={1.25} />
          </div>
        )}
        {product.discount_rate > 0 && (
          <span
            className={`absolute left-2 top-2 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white shadow ${
              product.is_liquidation ? "bg-rose-600" : "bg-amber-500"
            }`}
          >
            {product.is_liquidation ? "Liquidation" : `−${product.discount_rate}%`}
          </span>
        )}
        {showStaffBadge && !product.is_active && (
          <span className="absolute right-2 top-2 rounded bg-madec-text/80 px-2 py-0.5 text-[10px] font-medium text-white">
            Inactif
          </span>
        )}
      </button>
      <div className="flex flex-1 flex-col p-4">
        <p className="text-[10px] font-mono uppercase tracking-wide text-madec-muted">
          {product.product_code}
        </p>
        <button
          type="button"
          onClick={() => onView(product)}
          className="mt-0.5 line-clamp-2 text-left text-sm font-semibold text-madec-text transition-colors group-hover:text-madec-primary"
        >
          {product.name}
        </button>
        <div className="mt-auto flex items-end justify-between pt-3">
          <ProductPrice
            basePrice={product.base_price}
            finalPrice={product.final_price}
            discountRate={product.discount_rate}
            unit={product.unit}
          />
          {showCart && (
            <button
              type="button"
              onClick={() => onAddToCart(product)}
              className="btn-primary btn-sm relative shadow-sm"
              disabled={!product.is_active}
              title="Ajouter au panier"
            >
              <ShoppingCart size={14} />
              {cartQty > 0 && (
                <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500 px-1 text-[10px] font-bold text-white">
                  {cartQty}
                </span>
              )}
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
