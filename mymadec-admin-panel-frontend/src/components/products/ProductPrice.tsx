import { formatMAD } from "../../lib/labels";

interface ProductPriceProps {
  basePrice: number | null;
  finalPrice: number | null;
  discountRate: number;
  unit?: string | null;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "text-base",
  md: "text-lg",
  lg: "text-xl",
} as const;

export function ProductPrice({
  basePrice,
  finalPrice,
  discountRate,
  unit,
  size = "md",
}: ProductPriceProps) {
  return (
    <div>
      {discountRate > 0 && basePrice != null && (
        <p className="text-xs text-madec-muted line-through">{formatMAD(basePrice)}</p>
      )}
      <p className={`font-bold text-madec-primary ${sizeClasses[size]}`}>
        {finalPrice != null ? formatMAD(finalPrice) : "—"}
      </p>
      {unit && <p className="text-[10px] text-madec-muted">/ {unit}</p>}
    </div>
  );
}
