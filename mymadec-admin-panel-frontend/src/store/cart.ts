import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Product } from "../lib/types";

export interface CartItem {
  product: Product;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  add: (product: Product, qty?: number) => void;
  remove: (productId: number) => void;
  setQty: (productId: number, qty: number) => void;
  clear: () => void;
  total: () => number;
  /** Number of distinct products in the cart (for badges). */
  count: () => number;
  /** Sum of all line quantities. */
  totalQty: () => number;
}

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],

      add: (product, qty = 1) => {
        set((s) => {
          const existing = s.items.find((i) => i.product.id === product.id);
          if (existing) {
            return {
              items: s.items.map((i) =>
                i.product.id === product.id ? { ...i, quantity: i.quantity + qty } : i,
              ),
            };
          }
          return { items: [...s.items, { product, quantity: qty }] };
        });
      },

      remove: (productId) =>
        set((s) => ({ items: s.items.filter((i) => i.product.id !== productId) })),

      setQty: (productId, qty) => {
        if (qty <= 0) {
          get().remove(productId);
          return;
        }
        set((s) => ({
          items: s.items.map((i) =>
            i.product.id === productId ? { ...i, quantity: qty } : i,
          ),
        }));
      },

      clear: () => set({ items: [] }),

      total: () =>
        get().items.reduce((sum, i) => sum + (i.product.final_price ?? 0) * i.quantity, 0),

      count: () => get().items.length,

      totalQty: () => get().items.reduce((sum, i) => sum + i.quantity, 0),
    }),
    { name: "mymadec-cart" },
  ),
);
