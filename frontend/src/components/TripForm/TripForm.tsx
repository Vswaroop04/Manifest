import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Navigation, Package, PackageCheck, Clock, Timer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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
  departure_time: z.string().refine((v) => {
    if (!v) return false;
    return new Date(v) > new Date();
  }, "form.errors.departurePast"),
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

function FieldError({ message }: { message?: string }) {
  const { t } = useTranslation();
  if (!message) return null;
  const translated = message.startsWith("form.errors.") ? t(message) : message;
  return (
    <p className="mt-1 text-xs" style={{ color: "var(--red)" }}>
      {translated}
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
    defaultValues: {
      current_location: "",
      pickup_location: "",
      dropoff_location: "",
      cycle_hours_used: 0,
      departure_time: defaultDeparture(),
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      <div
        className="rounded-xl border p-5 flex flex-col gap-5"
        style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
      >
        <div
          className="text-xs font-medium uppercase tracking-widest pb-2 border-b"
          style={{ color: "var(--text-dim)", borderColor: "var(--border)" }}
        >
          {t("form.title")}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="current_location" className="flex items-center gap-1.5">
            <Navigation size={11} style={{ color: "var(--cyan)" }} />
            {t("form.currentLocation.label")}
          </Label>
          <Controller
            control={control}
            name="current_location"
            render={({ field }) => (
              <AddressInput
                id="current_location"
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
                placeholder={t("form.currentLocation.placeholder")}
                error={errors.current_location?.message
                  ? (errors.current_location.message.startsWith("form.errors.")
                    ? t(errors.current_location.message)
                    : errors.current_location.message)
                  : undefined}
              />
            )}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="pickup_location" className="flex items-center gap-1.5">
            <Package size={11} style={{ color: "var(--amber)" }} />
            {t("form.pickupLocation.label")}
          </Label>
          <Controller
            control={control}
            name="pickup_location"
            render={({ field }) => (
              <AddressInput
                id="pickup_location"
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
                placeholder={t("form.pickupLocation.placeholder")}
                error={errors.pickup_location?.message
                  ? (errors.pickup_location.message.startsWith("form.errors.")
                    ? t(errors.pickup_location.message)
                    : errors.pickup_location.message)
                  : undefined}
              />
            )}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="dropoff_location" className="flex items-center gap-1.5">
            <PackageCheck size={11} style={{ color: "var(--green)" }} />
            {t("form.dropoffLocation.label")}
          </Label>
          <Controller
            control={control}
            name="dropoff_location"
            render={({ field }) => (
              <AddressInput
                id="dropoff_location"
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
                placeholder={t("form.dropoffLocation.placeholder")}
                error={errors.dropoff_location?.message
                  ? (errors.dropoff_location.message.startsWith("form.errors.")
                    ? t(errors.dropoff_location.message)
                    : errors.dropoff_location.message)
                  : undefined}
              />
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cycle_hours_used" className="flex items-center gap-1.5">
              <Timer size={11} style={{ color: "var(--orange)" }} />
              {t("form.cycleHours.label")}
            </Label>
            <Input
              id="cycle_hours_used"
              type="number"
              step="0.5"
              min={0}
              max={70}
              placeholder={t("form.cycleHours.placeholder")}
              {...register("cycle_hours_used", { valueAsNumber: true })}
              className={errors.cycle_hours_used ? "border-[var(--red)]" : ""}
            />
            <p className="text-xs" style={{ color: "var(--text-dim)" }}>
              {t("form.cycleHours.hint")}
            </p>
            <FieldError message={errors.cycle_hours_used?.message} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="departure_time" className="flex items-center gap-1.5">
              <Clock size={11} style={{ color: "var(--cyan)" }} />
              {t("form.departureTime.label")}
            </Label>
            <Input
              id="departure_time"
              type="datetime-local"
              {...register("departure_time")}
              className={errors.departure_time ? "border-[var(--red)]" : ""}
              style={{
                colorScheme: "dark",
                fontFamily: "var(--font-mono)",
                fontSize: "0.75rem",
              }}
            />
            <FieldError message={errors.departure_time?.message} />
          </div>
        </div>
      </div>

      <Button type="submit" size="lg" disabled={isPending} className="w-full font-semibold tracking-wide">
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
