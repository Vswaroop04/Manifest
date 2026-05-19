import { useEffect, useRef, useState } from "react";
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
  const [text, setText] = useState<string>(value.toString());
  const [focused, setFocused] = useState(false);
  const holdTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!focused) setText(value.toString());
  }, [value, focused]);

  function clamp(n: number) {
    return Math.min(max, Math.max(min, n));
  }

  function adjust(delta: number) {
    const next = clamp(parseFloat((value + delta).toFixed(2)));
    onChange(next);
    setText(next.toString());
  }

  function startHold(delta: number) {
    adjust(delta);
    holdTimer.current = setInterval(() => {
      const next = clamp(parseFloat((value + delta).toFixed(2)));
      onChange(next);
      setText(next.toString());
    }, 120);
  }

  function stopHold() {
    if (holdTimer.current) {
      clearInterval(holdTimer.current);
      holdTimer.current = null;
    }
  }

  function handleFocus() {
    setFocused(true);
    if (value === 0) setText("");
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value.replace(/[^0-9.]/g, "");
    setText(raw);
    if (raw === "") {
      onChange(0);
      return;
    }
    const v = parseFloat(raw);
    if (!isNaN(v)) onChange(v);
  }

  function handleBlur() {
    setFocused(false);
    const v = parseFloat(text);
    if (isNaN(v)) {
      onChange(0);
      setText("0");
    } else {
      const c = clamp(v);
      onChange(c);
      setText(c.toString());
    }
    onBlur?.();
  }

  const overMax = value > max;
  const underMin = value < min;
  const invalid = overMax || underMin || error;

  return (
    <div className="relative">
      <input
        id={id}
        type="text"
        inputMode="decimal"
        value={text}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        className={cn(
          "flex h-14 w-full rounded-xl border bg-[var(--bg-card)] pl-6 pr-14 py-3 text-[15px] text-[var(--text)] placeholder:text-[var(--text-dim)] focus:outline-none focus:ring-2 transition-colors",
          invalid
            ? "border-[var(--red)] focus:border-[var(--red)] focus:ring-[rgba(255,23,68,0.15)]"
            : "border-[var(--border)] focus:border-[var(--orange)] focus:ring-[var(--orange-dim)]"
        )}
        style={{ fontFamily: "var(--font-mono)" }}
      />
      <div
        className="absolute right-1.5 top-1.5 bottom-1.5 flex flex-col rounded-md overflow-hidden border border-[var(--border)]"
        style={{ background: "var(--bg-card)" }}
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
          className="flex items-center justify-center w-8 flex-1 hover:bg-[var(--bg-hover)] disabled:opacity-30 disabled:hover:bg-transparent transition-colors cursor-pointer"
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
          className="flex items-center justify-center w-8 flex-1 hover:bg-[var(--bg-hover)] disabled:opacity-30 disabled:hover:bg-transparent transition-colors cursor-pointer"
          style={{ color: "var(--text-secondary)" }}
        >
          <ChevronDown size={14} />
        </button>
      </div>

      {(overMax || underMin) && (
        <p className="text-xs mt-1.5" style={{ color: "var(--red)" }}>
          {overMax ? `Max ${max} hours` : `Min ${min} hours`}
        </p>
      )}
    </div>
  );
}
