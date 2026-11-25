interface FilterChipsProps<T extends string> {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}

export function FilterChips<T extends string>({ options, value, onChange }: FilterChipsProps<T>) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt.value || "__all"}
          type="button"
          onClick={() => onChange(opt.value)}
          className={`filter-chip ${value === opt.value ? "filter-chip-active" : ""}`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
