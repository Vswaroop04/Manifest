import { useEffect, useRef, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Clock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AddressInput } from "./AddressInput";
import { NumberStepper } from "./NumberStepper";
import { useTranslation } from "@/hooks/useTranslation";

const TIME_OPTIONS: { label: string; value: string }[] = Array.from({ length: 48 }, (_, i) => {
  const h = Math.floor(i / 2);
  const m = i % 2 === 0 ? "00" : "30";
  const ampm = h < 12 ? "AM" : "PM";
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return {
    label: `${h12}:${m} ${ampm}`,
    value: `${String(h).padStart(2, "0")}:${m}`,
  };
});

function TimeDropdown({
  value,
  onChange,
  error,
}: {
  value: string;
  onChange: (v: string) => void;
  error: boolean;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const selected = TIME_OPTIONS.find((o) => o.value === value) ?? TIME_OPTIONS[16];

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    if (open && listRef.current) {
      const idx = TIME_OPTIONS.findIndex((o) => o.value === value);
      const item = listRef.current.children[idx] as HTMLElement | undefined;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [open, value]);

  return (
    <div ref={containerRef} className="relative" style={{ minWidth: 130 }}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        className="flex items-center gap-2 w-full h-14 px-4 rounded-xl border transition-colors"
        style={{
          background: "var(--bg-card)",
          borderColor: open ? "var(--orange)" : error ? "var(--red)" : "var(--border)",
          color: "var(--text)",
          fontFamily: "var(--font-mono)",
          fontSize: "0.85rem",
        }}
      >
        <Clock size={14} style={{ color: "var(--text-dim)", flexShrink: 0 }} />
        <span className="flex-1 text-left">{selected.label}</span>
        <svg
          width="10" height="6" viewBox="0 0 10 6" fill="none"
          style={{
            color: "var(--text-dim)",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.15s",
            flexShrink: 0,
          }}
        >
          <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <ul
          ref={listRef}
          className="absolute z-[100] w-full mt-2 rounded-xl border border-[var(--border-bright)] overflow-y-auto shadow-2xl"
          style={{ background: "var(--bg-elevated)", maxHeight: 220 }}
        >
          {TIME_OPTIONS.map((o) => {
            const isSelected = o.value === value;
            return (
              <li
                key={o.value}
                onMouseDown={() => { onChange(o.value); setOpen(false); }}
                className="flex items-center gap-3 px-4 py-3 text-[15px] cursor-pointer transition-colors"
                style={{
                  color: isSelected ? "var(--orange)" : "var(--text)",
                  background: isSelected ? "var(--orange-dim)" : "transparent",
                  fontFamily: "var(--font-mono)",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) e.currentTarget.style.background = "var(--bg-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = isSelected ? "var(--orange-dim)" : "transparent";
                }}
              >
                <Clock size={13} style={{ color: isSelected ? "var(--orange)" : "var(--text-dim)", flexShrink: 0 }} />
                {o.label}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

interface DeparturePickerProps {
  value: string;
  onChange: (v: string) => void;
  error: boolean;
}

function DeparturePicker({ value, onChange, error }: DeparturePickerProps) {
  const [datePart, timePart] = value.includes("T") ? value.split("T") : [value, "08:00"];
  const timeValue = timePart.slice(0, 5);

  const borderColor = error ? "var(--red)" : "var(--border)";
  const focusBorder = error ? "var(--red)" : "var(--orange)";

  return (
    <div className="flex gap-2">
      <input
        type="date"
        value={datePart}
        min={new Date().toISOString().slice(0, 10)}
        onChange={(e) => onChange(`${e.target.value}T${timeValue}`)}
        style={{
          flex: 1,
          height: 56,
          background: "var(--bg-card)",
          border: `1px solid ${borderColor}`,
          borderRadius: 12,
          color: "var(--text)",
          fontFamily: "var(--font-mono)",
          fontSize: "0.85rem",
          padding: "0 16px",
          outline: "none",
          transition: "border-color 0.15s",
          colorScheme: "dark",
        }}
        onFocus={(e) => (e.currentTarget.style.borderColor = focusBorder)}
        onBlur={(e) => (e.currentTarget.style.borderColor = borderColor)}
      />
      <TimeDropdown
        value={timeValue}
        onChange={(t) => onChange(`${datePart}T${t}`)}
        error={error}
      />
    </div>
  );
}

const schema = z.object({
  current_location: z.string().min(2, "form.errors.currentLocationRequired"),
  pickup_location: z.string().min(2, "form.errors.pickupLocationRequired"),
  dropoff_location: z.string().min(2, "form.errors.dropoffLocationRequired"),
  cycle_hours_used: z
    .number({ invalid_type_error: "form.errors.cycleHoursRequired" })
    .min(0, "form.errors.cycleHoursMin")
    .max(70, "form.errors.cycleHoursMax"),
  departure_time: z
    .string()
    .refine(
      (v) => !!v && new Date(v) > new Date(),
      "form.errors.departurePast",
    ),
});

export type TripFormValues = z.infer<typeof schema>;

export interface TripFormInitialValues {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  cycle_hours_used: number;
  departure_time: string; // ISO datetime from backend
}

interface TripFormProps {
  onSubmit: (values: TripFormValues) => void;
  isPending: boolean;
  initialValues?: TripFormInitialValues;
}

function toLocalDateTimeString(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}

function defaultDeparture(): string {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setSeconds(0, 0);
  return toLocalDateTimeString(d);
}


function FieldLabel({
  children,
  color,
}: {
  children: React.ReactNode;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span
        className="block w-1.5 h-1.5 rounded-full shrink-0"
        style={{ background: color, boxShadow: `0 0 6px ${color}` }}
      />
      <span
        className="text-[11px] font-semibold tracking-widest uppercase"
        style={{ color: "var(--text-dim)" }}
      >
        {children}
      </span>
    </div>
  );
}

function FieldError({ message }: { message?: string }) {
  const { t } = useTranslation();
  if (!message) return null;
  const text = message.startsWith("form.errors.") ? t(message) : message;
  return (
    <p className="text-xs mt-1.5" style={{ color: "var(--red)" }}>
      {text}
    </p>
  );
}

export function TripForm({ onSubmit, isPending, initialValues }: TripFormProps) {
  const { t } = useTranslation();
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<TripFormValues>({
    resolver: zodResolver(schema),
    mode: "onChange",
    defaultValues: {
      current_location: "",
      pickup_location: "",
      dropoff_location: "",
      cycle_hours_used: 0,
      departure_time: defaultDeparture(),
    },
  });

  useEffect(() => {
    if (initialValues) {
      reset({
        current_location: initialValues.current_location,
        pickup_location: initialValues.pickup_location,
        dropoff_location: initialValues.dropoff_location,
        cycle_hours_used: initialValues.cycle_hours_used,
        departure_time: initialValues.departure_time.slice(0, 16),
      });
    } else {
      reset({
        current_location: "",
        pickup_location: "",
        dropoff_location: "",
        cycle_hours_used: 0,
        departure_time: defaultDeparture(),
      });
    }
  }, [initialValues, reset]);

  function errMsg(msg?: string) {
    if (!msg) return undefined;
    return msg.startsWith("form.errors.") ? t(msg) : msg;
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-5 pt-1 px-2"
      noValidate
    >
      {/* Current location */}
      <div>
        <FieldLabel color="var(--cyan)">Current location</FieldLabel>
        <Controller
          control={control}
          name="current_location"
          render={({ field }) => (
            <AddressInput
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              placeholder={t("form.currentLocation.placeholder")}
              error={errMsg(errors.current_location?.message)}
            />
          )}
        />
      </div>

      {/* Pickup location */}
      <div>
        <FieldLabel color="var(--amber)">Pickup location</FieldLabel>
        <Controller
          control={control}
          name="pickup_location"
          render={({ field }) => (
            <AddressInput
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              placeholder={t("form.pickupLocation.placeholder")}
              error={errMsg(errors.pickup_location?.message)}
            />
          )}
        />
      </div>

      {/* Dropoff location */}
      <div>
        <FieldLabel color="var(--green)">Dropoff location</FieldLabel>
        <Controller
          control={control}
          name="dropoff_location"
          render={({ field }) => (
            <AddressInput
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              placeholder={t("form.dropoffLocation.placeholder")}
              error={errMsg(errors.dropoff_location?.message)}
            />
          )}
        />
      </div>

      {/* Cycle used */}
      <div>
        <FieldLabel color="var(--orange)">Cycle used</FieldLabel>
          <Controller
            control={control}
            name="cycle_hours_used"
            render={({ field }) => (
              <NumberStepper
                value={field.value ?? 0}
                onChange={field.onChange}
                onBlur={field.onBlur}
                min={0}
                max={70}
                step={0.5}
                placeholder="0"
                error={!!errors.cycle_hours_used}
              />
            )}
          />
          <p className="text-[11px] mt-2" style={{ color: "var(--text-dim)" }}>
            hours · 70-hr cycle
          </p>
          <FieldError message={errors.cycle_hours_used?.message} />
      </div>

      {/* Departure */}
      <div>
        <FieldLabel color="var(--cyan)">Departure</FieldLabel>
        <Controller
          control={control}
          name="departure_time"
          render={({ field }) => (
            <DeparturePicker
              value={field.value}
              onChange={field.onChange}
              error={!!errors.departure_time}
            />
          )}
        />
        <p className="text-[11px] mt-2" style={{ color: "var(--text-dim)" }}>
          must be in the future
        </p>
        <FieldError message={errors.departure_time?.message} />
      </div>

      <Button
        type="submit"
        size="lg"
        disabled={isPending || (!!initialValues && !isDirty)}
        className="w-full font-bold tracking-widest mt-1"
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "1rem",
          height: "54px",
        }}
      >
        {isPending ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            {t("form.submitting")}
          </>
        ) : (
          t("form.submit")
        )}
      </Button>
    </form>
  );
}
