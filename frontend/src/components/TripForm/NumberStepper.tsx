import { useRef } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface NumberStepperProps {
  value: number;
  onChange: (value: number) => void;
  onBlur?: () => void;
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  error?: boolean;
  id?: string;
}

export function NumberStepper({
  value,
  onChange,
  onBlur,
  min = 0,
  max = 100,
  step = 1,
  placeholder,
  error,
  id,
}: NumberStepperProps) {
  const holdTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  function clamp(n: number) {
    return Math.min(max, Math.max(min, n));
  }

  function adjust(delta: number) {
    const next = clamp(parseFloat((value + delta).toFixed(2)));
    onChange(next);
  }

  function startHold(delta: number) {
    adjust(delta);
    holdTimer.current = setInterval(() => adjust(delta), 120);
  }

  function stopHold() {
    if (holdTimer.current) {
      clearInterval(holdTimer.current);
      holdTimer.current = null;
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    if (raw === "") {
      onChange(0);
      return;
    }
    const v = parseFloat(raw);
    if (!isNaN(v)) onChange(v);
  }

  function handleBlur() {
    if (value < min || value > max) onChange(clamp(value));
    onBlur?.();
  }

  const overMax = value > max;
  const underMin = value < min;
  const invalid = overMax || underMin || error;

  return (
    <div className="relative">
      <input
        id={id}
        type="number"
        inputMode="decimal"
        value={value}
        onChange={handleInput}
        onBlur={handleBlur}
        min={min}
        max={max}
        step={step}
        placeholder={placeholder}
        className={cn(
          "flex h-12 w-full rounded-lg border bg-[var(--bg-card)] pl-4 pr-12 py-3 text-base text-[var(--text)] placeholder:text-[var(--text-dim)] focus:outline-none focus:ring-2 transition-colors",
          invalid
            ? "border-[var(--red)] focus:border-[var(--red)] focus:ring-[rgba(255,23,68,0.15)]"
            : "border-[var(--border)] focus:border-[var(--orange)] focus:ring-[var(--orange-dim)]"
        )}
        style={{ fontFamily: "var(--font-mono)" }}
      />
      <div
        className="absolute right-1.5 top-1.5 bottom-1.5 flex flex-col rounded-md overflow-hidden"
        style={{ background: "var(--bg-elevated)" }}
      >
        <button
          type="button"
          aria-label="Increase"
          disabled={value >= max}
          onMouseDown={() => startHold(step)}
          onMouseUp={stopHold}
          onMouseLeave={stopHold}
          onTouchStart={() => startHold(step)}
          onTouchEnd={stopHold}
          className="flex items-center justify-center w-7 flex-1 hover:bg-[var(--bg-hover)] disabled:opacity-30 disabled:hover:bg-transparent transition-colors cursor-pointer"
          style={{ color: "var(--text-secondary)" }}
        >
          <ChevronUp size={14} />
        </button>
        <div style={{ height: 1, background: "var(--border)" }} />
        <button
          type="button"
          aria-label="Decrease"
          disabled={value <= min}
          onMouseDown={() => startHold(-step)}
          onMouseUp={stopHold}
          onMouseLeave={stopHold}
          onTouchStart={() => startHold(-step)}
          onTouchEnd={stopHold}
          className="flex items-center justify-center w-7 flex-1 hover:bg-[var(--bg-hover)] disabled:opacity-30 disabled:hover:bg-transparent transition-colors cursor-pointer"
          style={{ color: "var(--text-secondary)" }}
        >
          <ChevronDown size={14} />
        </button>
      </div>

      {overMax && (
        <p className="text-xs mt-1.5" style={{ color: "var(--red)" }}>
          Max {max} hours
        </p>
      )}
      {underMin && (
        <p className="text-xs mt-1.5" style={{ color: "var(--red)" }}>
          Min {min} hours
        </p>
      )}
    </div>
  );
}
