/** Text input with datalist — pick from managed values or type a custom one. */
interface ComboSelectProps {
  id: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function ComboSelect({
  id,
  value,
  onChange,
  options,
  placeholder,
  className = "input",
  disabled,
}: ComboSelectProps) {
  const unique = [...new Set(options.filter(Boolean))];
  return (
    <>
      <input
        id={id}
        list={`${id}-list`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={className}
        disabled={disabled}
      />
      <datalist id={`${id}-list`}>
        {unique.map((o) => (
          <option key={o} value={o} />
        ))}
      </datalist>
    </>
  );
}
