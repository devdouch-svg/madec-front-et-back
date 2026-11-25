import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  /** Less padding — compact dialogs */
  dense?: boolean;
}

export function Modal({ open, onClose, title, children, size = "md", dense = false }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      prev?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  const w = { sm: "max-w-sm", md: "max-w-lg", lg: "max-w-2xl" }[size];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-madec-text/40 backdrop-blur-sm"
        aria-label="Fermer"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`relative w-full ${w} overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-madec-border outline-none`}
      >
        <div
          className={`flex items-center justify-between border-b border-madec-border bg-madec-active/50 ${
            dense ? "px-4 py-3" : "px-6 py-4"
          }`}
        >
          <h2 id={titleId} className={`font-semibold text-madec-text ${dense ? "line-clamp-1 text-sm" : "text-base"}`}>
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer la fenêtre"
            className="btn-icon"
          >
            <X size={18} />
          </button>
        </div>
        <div className={dense ? "p-4" : "p-6"}>{children}</div>
      </div>
    </div>
  );
}
