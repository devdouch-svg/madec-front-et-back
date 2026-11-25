import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  page: number;
  pages: number;
  total: number;
  pageSize: number;
  onChange: (p: number) => void;
}

export function Pagination({ page, pages, total, pageSize, onChange }: Props) {
  if (total === 0) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-madec-border px-4 py-3">
      <span className="text-sm text-madec-muted">
        {from}–{to} sur {total}
      </span>
      {pages > 1 && (
        <div className="flex gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page === 1}
          className="btn-icon disabled:opacity-40"
        >
          <ChevronLeft size={16} />
        </button>
        {Array.from({ length: Math.min(pages, 7) }, (_, i) => {
          const p = i + 1;
          return (
            <button
              key={p}
              onClick={() => onChange(p)}
              className={`rounded-lg px-3 py-1 text-sm transition-colors ${
                p === page ? "bg-madec-primary text-white" : "text-madec-secondary hover:bg-madec-tint"
              }`}
            >
              {p}
            </button>
          );
        })}
        <button
          onClick={() => onChange(page + 1)}
          disabled={page === pages}
          className="btn-icon disabled:opacity-40"
        >
          <ChevronRight size={16} />
        </button>
        </div>
      )}
    </div>
  );
}
