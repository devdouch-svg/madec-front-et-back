/** Strict dropdown — values must come from the referential (no free text). */
interface CatalogSelectProps {
  id: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function CatalogSelect({
  id,
  value,
  onChange,
  options,
  placeholder = "Choisir…",
  className = "input",
  disabled,
}: CatalogSelectProps) {
  const unique = [...new Set(options.filter(Boolean))];
  return (
    <select
      id={id}
      className={className}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{placeholder}</option>
      {unique.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}
