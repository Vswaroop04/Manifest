import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AddressInput } from "./AddressInput";
import { useTranslation } from "@/hooks/useTranslation";

const schema = z.object({
  current_location: z.string().min(2, "form.errors.currentLocationRequired"),
  pickup_location: z.string().min(2, "form.errors.pickupLocationRequired"),
  dropoff_location: z.string().min(2, "form.errors.dropoffLocationRequired"),
  cycle_hours_used: z
    .number({ invalid_type_error: "form.errors.cycleHoursRequired" })
    .min(0, "form.errors.cycleHoursMin")
    .max(70, "form.errors.cycleHoursMax"),
  departure_time: z.string().refine((v) => !!v && new Date(v) > new Date(), "form.errors.departurePast"),
});

export type TripFormValues = z.infer<typeof schema>;

interface TripFormProps {
  onSubmit: (values: TripFormValues) => void;
  isPending: boolean;
}

function defaultDeparture(): string {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setSeconds(0, 0);
  return d.toISOString().slice(0, 16);
}

function FieldLabel({ children, accent }: { children: React.ReactNode; accent?: string }) {
  return (
    <p
      className="text-[11px] font-semibold uppercase tracking-[0.08em] mb-1"
      style={{ color: accent ?? "var(--text-secondary)" }}
    >
      {children}
    </p>
  );
}

function FieldError({ message }: { message?: string }) {
  const { t } = useTranslation();
  if (!message) return null;
  const text = message.startsWith("form.errors.") ? t(message) : message;
  return <p className="text-[11px] mt-1" style={{ color: "var(--red)" }}>{text}</p>;
}

export function TripForm({ onSubmit, isPending }: TripFormProps) {
  const { t } = useTranslation();
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TripFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      current_location: "",
      pickup_location: "",
      dropoff_location: "",
      cycle_hours_used: 0,
      departure_time: defaultDeparture(),
    },
  });

  function errMsg(msg?: string) {
    if (!msg) return undefined;
    return msg.startsWith("form.errors.") ? t(msg) : msg;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">

      {/* Route fields */}
      <div
        className="rounded-xl border overflow-hidden"
        style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
      >
        {/* Current location */}
        <div
          className="px-4 pt-4 pb-3 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <FieldLabel accent="var(--cyan)">Current location</FieldLabel>
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

        {/* Pickup */}
        <div
          className="px-4 pt-3 pb-3 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <FieldLabel accent="var(--amber)">Pickup location</FieldLabel>
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

        {/* Dropoff */}
        <div className="px-4 pt-3 pb-4">
          <FieldLabel accent="var(--green)">Dropoff location</FieldLabel>
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
      </div>

      {/* Cycle + Departure row */}
      <div className="grid grid-cols-2 gap-3">
        <div
          className="rounded-xl border px-4 pt-3 pb-4"
          style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
        >
          <FieldLabel accent="var(--orange)">Cycle used</FieldLabel>
          <Input
            type="number"
            step="0.5"
            min={0}
            max={70}
            placeholder="0 – 70"
            {...register("cycle_hours_used", { valueAsNumber: true })}
            className={errors.cycle_hours_used ? "border-[var(--red)]" : ""}
            style={{ fontFamily: "var(--font-mono)" }}
          />
          <p className="text-[10px] mt-1.5" style={{ color: "var(--text-dim)" }}>
            hrs · 70-hr cycle
          </p>
          <FieldError message={errors.cycle_hours_used?.message} />
        </div>

        <div
          className="rounded-xl border px-4 pt-3 pb-4"
          style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
        >
          <FieldLabel accent="var(--cyan)">Departure</FieldLabel>
          <Input
            type="datetime-local"
            {...register("departure_time")}
            className={errors.departure_time ? "border-[var(--red)]" : ""}
            style={{
              colorScheme: "dark",
              fontFamily: "var(--font-mono)",
              fontSize: "0.7rem",
              paddingLeft: "8px",
              paddingRight: "4px",
            }}
          />
          <FieldError message={errors.departure_time?.message} />
        </div>
      </div>

      <Button
        type="submit"
        size="lg"
        disabled={isPending}
        className="w-full font-semibold tracking-wide"
        style={{ fontFamily: "var(--font-display)", fontSize: "1rem", letterSpacing: "0.1em" }}
      >
        {isPending ? (
          <>
            <Loader2 size={15} className="animate-spin" />
            {t("form.submitting")}
          </>
        ) : (
          t("form.submit")
        )}
      </Button>
    </form>
  );
}
