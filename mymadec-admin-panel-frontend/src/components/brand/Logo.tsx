import logoDarkBg from "../../assets/madec-1.png";
import logoLightBg from "../../assets/madec-vo.png";

type LogoSize = "sm" | "md" | "lg" | "xl";

const heights: Record<LogoSize, string> = {
  sm: "h-7",
  md: "h-9",
  lg: "h-10",
  xl: "h-12",
};

interface LogoProps {
  size?: LogoSize;
  className?: string;
  /** dark = sidebar / blue panel; light = white background */
  on?: "dark" | "light";
}

export function Logo({ size = "md", className = "", on = "dark" }: LogoProps) {
  const src = on === "dark" ? logoDarkBg : logoLightBg;
  const isCustom = className.includes("sidebar-logo") || className.includes("auth-logo");
  return (
    <img
      src={src}
      alt="MADEC"
      className={
        isCustom
          ? className
          : `${heights[size]} w-auto max-w-full object-contain object-left ${className}`
      }
    />
  );
}
