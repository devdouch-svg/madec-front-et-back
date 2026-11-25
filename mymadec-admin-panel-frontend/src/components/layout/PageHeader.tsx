import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  /** Alias for actions — badge or toolbar on the right */
  meta?: ReactNode;
}

export function PageHeader({ title, subtitle, actions, meta }: PageHeaderProps) {
  const right = actions ?? meta;
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-madec-border pb-4">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {right && <div className="flex flex-wrap items-center gap-2">{right}</div>}
    </div>
  );
}
