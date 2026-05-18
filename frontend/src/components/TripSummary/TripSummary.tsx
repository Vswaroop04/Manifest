import { Route, Clock, CalendarDays, Gauge, AlertTriangle } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";

interface Props {
  totalMiles: number;
  totalDriveSecs: number;
  totalDays: number;
  cycleHoursAfter: number;
  usedFallback: boolean;
}

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div
      className="flex flex-col gap-1.5 rounded-lg p-3 border"
      style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
    >
      <div className="flex items-center gap-1.5" style={{ color: "var(--text-secondary)" }}>
        {icon}
        <span className="text-xs uppercase tracking-wider">{label}</span>
      </div>
      <span
        className="text-xl font-semibold"
        style={{ fontFamily: "var(--font-mono)", color: accent ?? "var(--text)" }}
      >
        {value}
      </span>
    </div>
  );
}

function formatMiles(m: number) {
  return m.toLocaleString("en-US", { maximumFractionDigits: 0 }) + " mi";
}

function formatDrive(secs: number) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

function cycleColor(hrs: number) {
  if (hrs >= 60) return "var(--red)";
  if (hrs >= 48) return "var(--amber)";
  return "var(--green)";
}

export function TripSummary({
  totalMiles,
  totalDriveSecs,
  totalDays,
  cycleHoursAfter,
  usedFallback,
}: Props) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-3">
      <div
        className="text-xs font-medium uppercase tracking-widest pb-2 border-b"
        style={{ color: "var(--text-dim)", borderColor: "var(--border)" }}
      >
        {t("summary.title")}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <StatCard
          icon={<Route size={12} />}
          label={t("summary.totalMiles")}
          value={formatMiles(totalMiles)}
          accent="var(--cyan)"
        />
        <StatCard
          icon={<Clock size={12} />}
          label={t("summary.drivingTime")}
          value={formatDrive(totalDriveSecs)}
        />
        <StatCard
          icon={<CalendarDays size={12} />}
          label={t("summary.totalDays")}
          value={`${totalDays} day${totalDays !== 1 ? "s" : ""}`}
        />
        <StatCard
          icon={<Gauge size={12} />}
          label={t("summary.cycleAfter")}
          value={`${cycleHoursAfter.toFixed(1)}h`}
          accent={cycleColor(cycleHoursAfter)}
        />
      </div>

      {usedFallback && (
        <div
          className="flex items-start gap-2 rounded-lg px-3 py-2.5 text-xs border"
          style={{
            background: "rgba(255,171,0,0.08)",
            borderColor: "rgba(255,171,0,0.25)",
            color: "var(--amber)",
          }}
        >
          <AlertTriangle size={12} className="shrink-0 mt-0.5" />
          {t("summary.fallbackWarning")}
        </div>
      )}
    </div>
  );
}
