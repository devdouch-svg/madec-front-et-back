export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const s = { sm: "h-4 w-4", md: "h-6 w-6", lg: "h-10 w-10" }[size];
  return (
    <div className={`${s} animate-spin rounded-full border-2 border-madec-tint border-t-madec-primary`} />
  );
}

export function PageLoader() {
  return (
    <div className="flex h-full min-h-[50vh] flex-col items-center justify-center gap-3 py-20">
      <Spinner size="lg" />
      <p className="text-sm font-medium text-madec-muted">Chargement…</p>
    </div>
  );
}
