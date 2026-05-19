import { useEffect, useState } from "react";
import { ArrowRight, MapPin, Loader2, AlertCircle, Clock } from "lucide-react";
import { getTripList, type TripSummaryItem } from "@/services/api";

interface Props {
  onSelect: (id: string) => void;
  loadingId: string | null;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric", minute: "2-digit", hour12: true,
  });
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "completed" ? "var(--green)" :
    status === "failed"    ? "var(--red)"   :
    "var(--amber)";
  return (
    <span
      className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
      style={{ background: color, boxShadow: `0 0 5px ${color}` }}
    />
  );
}

export function TripHistory({ onSelect, loadingId }: Props) {
  const [trips, setTrips] = useState<TripSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTripList()
      .then(setTrips)
      .catch(() => setError("Could not load trip history"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 gap-2" style={{ color: "var(--text-dim)" }}>
        <Loader2 size={16} className="animate-spin" />
        <span className="text-sm">Loading history…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 py-8 px-2 text-sm" style={{ color: "var(--red)" }}>
        <AlertCircle size={15} />
        {error}
      </div>
    );
  }

  if (trips.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-14 text-center">
        <Clock size={28} style={{ color: "var(--text-dim)" }} />
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>No past trips yet</p>
        <p className="text-xs" style={{ color: "var(--text-dim)" }}>Plan a route to see it here</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {trips.map((trip) => {
        const isLoading = loadingId === trip.id;
        return (
          <button
            key={trip.id}
            onClick={() => onSelect(trip.id)}
            disabled={loadingId !== null}
            className="w-full text-left rounded-xl border px-4 py-3.5 transition-colors disabled:opacity-60"
            style={{
              background: "var(--bg-elevated)",
              borderColor: "var(--border)",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--border-bright)")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex flex-col gap-1.5 min-w-0">
                <div className="flex items-center gap-1.5 text-sm font-medium" style={{ color: "var(--text)" }}>
                  <MapPin size={12} style={{ color: "var(--orange)", flexShrink: 0 }} />
                  <span className="truncate">{trip.pickup_location}</span>
                  <ArrowRight size={11} style={{ color: "var(--text-dim)", flexShrink: 0 }} />
                  <span className="truncate">{trip.dropoff_location}</span>
                </div>
                <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                  <StatusDot status={trip.status} />
                  <span>{formatDate(trip.departure_time)}</span>
                  <span style={{ color: "var(--border-bright)" }}>·</span>
                  <span>{formatTime(trip.departure_time)}</span>
                </div>
              </div>
              <div className="shrink-0 mt-0.5">
                {isLoading
                  ? <Loader2 size={14} className="animate-spin" style={{ color: "var(--orange)" }} />
                  : <ArrowRight size={14} style={{ color: "var(--text-dim)" }} />
                }
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
