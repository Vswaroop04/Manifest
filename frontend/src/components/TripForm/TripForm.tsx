import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AddressInput } from "./AddressInput";
import { NumberStepper } from "./NumberStepper";
import { useTranslation } from "@/hooks/useTranslation";

const schema = z.object({
  current_location: z.string().min(2, "form.errors.currentLocationRequired"),
  pickup_location: z.string().min(2, "form.errors.pickupLocationRequired"),
  dropoff_location: z.string().min(2, "form.errors.dropoffLocationRequired"),
  cycle_hours_used: z
    .number({ invalid_type_error: "form.errors.cycleHoursRequired" })
    .min(0, "form.errors.cycleHoursMin")
    .max(70, "form.errors.cycleHoursMax"),
  departure_time: z.string().refine(
    (v) => !!v && new Date(v) > new Date(),
    "form.errors.departurePast"
  ),
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

function minDeparture(): string {
  const d = new Date();
  d.setSeconds(0, 0);
  return d.toISOString().slice(0, 16);
}

function FieldLabel({
  children,
  color,
}: {
  children: React.ReactNode;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span
        className="block w-1.5 h-1.5 rounded-full"
        style={{ background: color, boxShadow: `0 0 6px ${color}` }}
      />
      <span
        className="text-[13px] font-medium tracking-wide"
        style={{ color: "var(--text-secondary)" }}
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
    <p className="text-xs mt-2" style={{ color: "var(--red)" }}>
      {text}
    </p>
  );
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
    mode: "onChange",
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
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3 pt-2">
      {/* Route fields — separate cards so suggestion dropdown can overflow */}
      <div
        className="rounded-2xl border px-5 py-6"
        style={{
          borderColor: "var(--border-bright)",
          background: "var(--bg-elevated)",
        }}
      >
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

      <div
        className="rounded-2xl border px-5 py-6"
        style={{
          borderColor: "var(--border-bright)",
          background: "var(--bg-elevated)",
        }}
      >
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

      <div
        className="rounded-2xl border px-5 py-6"
        style={{
          borderColor: "var(--border-bright)",
          background: "var(--bg-elevated)",
        }}
      >
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

      {/* Cycle + Departure */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div
          className="rounded-2xl border px-5 py-5"
          style={{
            borderColor: "var(--border-bright)",
            background: "var(--bg-elevated)",
          }}
        >
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
          <p className="text-xs mt-2.5" style={{ color: "var(--text-dim)" }}>
            hours · 70-hr cycle
          </p>
          <FieldError message={errors.cycle_hours_used?.message} />
        </div>

        <div
          className="rounded-2xl border px-5 py-5"
          style={{
            borderColor: "var(--border-bright)",
            background: "var(--bg-elevated)",
          }}
        >
          <FieldLabel color="var(--cyan)">Departure</FieldLabel>
          <Input
            type="datetime-local"
            min={minDeparture()}
            {...register("departure_time")}
            className={errors.departure_time ? "border-[var(--red)]" : ""}
            style={{
              colorScheme: "dark",
              fontFamily: "var(--font-mono)",
              fontSize: "0.78rem",
              paddingLeft: "20px",
              paddingRight: "12px",
            }}
          />
          <p className="text-xs mt-2.5" style={{ color: "var(--text-dim)" }}>
            must be in the future
          </p>
          <FieldError message={errors.departure_time?.message} />
        </div>
      </div>

      <Button
        type="submit"
        size="lg"
        disabled={isPending}
        className="w-full font-bold tracking-widest mt-2"
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
