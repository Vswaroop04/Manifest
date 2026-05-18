import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

interface Suggestion {
  label: string;
}

interface AddressInputProps {
  value: string;
  onChange: (value: string) => void;
  onBlur: () => void;
  placeholder?: string;
  error?: string;
  id?: string;
}

async function fetchSuggestions(q: string): Promise<Suggestion[]> {
  if (q.length < 2) return [];
  try {
    const res = await fetch(`/api/geocode/?q=${encodeURIComponent(q)}`);
    if (!res.ok) return [];
    return (await res.json()) as Suggestion[];
  } catch {
    return [];
  }
}

export function AddressInput({
  value,
  onChange,
  onBlur,
  placeholder,
  error,
  id,
}: AddressInputProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!focused || value.length < 2) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      const results = await fetchSuggestions(value);
      setSuggestions(results);
      setOpen(results.length > 0);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, focused]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function select(label: string) {
    onChange(label);
    setOpen(false);
    setFocused(false);
  }

  return (
    <div ref={containerRef} className="relative">
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          setTimeout(() => setFocused(false), 150);
          onBlur();
        }}
        className={cn(
          error && "border-[var(--red)] focus:border-[var(--red)] focus:ring-[rgba(255,23,68,0.15)]"
        )}
      />

      {open && (
        <ul
          className="absolute z-50 w-full mt-1 rounded-lg border border-[var(--border-bright)] overflow-hidden shadow-xl"
          style={{ background: "var(--bg-elevated)" }}
        >
          {suggestions.map((s, i) => (
            <li
              key={i}
              onMouseDown={() => select(s.label)}
              className="flex items-center gap-2 px-3 py-2.5 text-sm cursor-pointer hover:bg-[var(--bg-hover)] transition-colors"
              style={{ color: "var(--text)" }}
            >
              <MapPin size={12} style={{ color: "var(--orange)", flexShrink: 0 }} />
              {s.label}
            </li>
          ))}
        </ul>
      )}

      {error && (
        <p className="mt-1 text-[11px]" style={{ color: "var(--red)" }}>
          {error}
        </p>
      )}
    </div>
  );
}
