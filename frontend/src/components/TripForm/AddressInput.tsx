import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { MapPin, Loader2, SearchX } from "lucide-react";
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
  const res = await fetch(`/api/geocode/?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error("geocode failed");
  return (await res.json()) as Suggestion[];
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
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!focused || value.length < 2) {
      setSuggestions([]);
      setOpen(false);
      setSearched(false);
      return;
    }
    setOpen(true);
    setLoading(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await fetchSuggestions(value);
        setSuggestions(results);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
        setSearched(true);
      }
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

      {loading && (
        <Loader2
          size={14}
          className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin pointer-events-none"
          style={{ color: "var(--text-dim)" }}
        />
      )}

      {open && (
        <ul
          className="absolute z-[100] w-full mt-1 rounded-lg border border-[var(--border-bright)] overflow-hidden shadow-2xl"
          style={{ background: "var(--bg-elevated)" }}
        >
          {loading && suggestions.length === 0 && (
            <li
              className="flex items-center gap-2 px-3 py-3 text-sm"
              style={{ color: "var(--text-dim)" }}
            >
              <Loader2 size={13} className="animate-spin" style={{ color: "var(--orange)" }} />
              Searching US addresses…
            </li>
          )}

          {!loading && searched && suggestions.length === 0 && (
            <li
              className="flex items-center gap-2 px-3 py-3 text-sm"
              style={{ color: "var(--text-dim)" }}
            >
              <SearchX size={13} />
              No US results for "{value}"
            </li>
          )}

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
        <p className="mt-1.5 text-xs" style={{ color: "var(--red)" }}>
          {error}
        </p>
      )}
    </div>
  );
}
