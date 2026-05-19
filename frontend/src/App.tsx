import { lazy, Suspense, useState } from "react";
import { Truck, RotateCcw, History } from "lucide-react";
import { TripForm, type TripFormValues } from "@/components/TripForm/TripForm";
import { TripSummary } from "@/components/TripSummary/TripSummary";
import { TripHistory } from "@/components/TripHistory/TripHistory";
import { LogSheet } from "@/components/LogSheet/LogSheet";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";
import { useTripStore } from "@/store/tripStore";
import { planTrip, getTripDetail, type TripPlanResponse } from "@/services/api";

const RouteMap = lazy(() =>
  import("@/components/RouteMap/RouteMap").then((m) => ({ default: m.RouteMap }))
);

export default function App() {
  const { t } = useTranslation();
  const { activeTab, setActiveTab } = useTripStore();
  const [isPending, setIsPending] = useState(false);
  const [result, setResult] = useState<TripPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistoryId, setLoadingHistoryId] = useState<string | null>(null);

  async function handleSubmit(values: TripFormValues) {
    setIsPending(true);
    setError(null);
    try {
      const data = await planTrip({
        current_location: values.current_location,
        pickup_location: values.pickup_location,
        dropoff_location: values.dropoff_location,
        cycle_hours_used: values.cycle_hours_used,
        // date-only field → send 8am so backend future-time check passes
        departure_time: values.departure_time,
      });
      setResult(data);
      setActiveTab("map");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsPending(false);
    }
  }

  async function loadHistoryTrip(id: string) {
    setLoadingHistoryId(id);
    setError(null);
    try {
      const data = await getTripDetail(id);
      setResult(data);
      setShowHistory(false);
      setActiveTab("map");
    } catch {
      setError("Could not load that trip");
    } finally {
      setLoadingHistoryId(null);
    }
  }

  const cycleAfter = result
    ? parseFloat(result.day_logs.at(-1)?.recap_70hr ?? "0")
    : 0;

  return (
    <div className="flex flex-col h-full">
      <header
        className="flex items-center justify-between px-5 py-3 border-b shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-3 ml-1">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0"
            style={{ background: "var(--orange-dim)", border: "1px solid rgba(255,87,34,0.4)" }}
          >
            <Truck size={17} style={{ color: "var(--orange)" }} />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className="text-xl tracking-widest"
              style={{ fontFamily: "var(--font-display)", color: "var(--text)" }}
            >
              {t("app.name")}
            </span>
            <span
              className="text-xs hidden sm:inline"
              style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}
            >
              {t("app.tagline")}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {result && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { setResult(null); setError(null); setShowHistory(false); setActiveTab("map"); }}
              className="gap-1.5 text-xs"
            >
              <RotateCcw size={13} />
              {t("nav.newTrip")}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowHistory((p) => !p)}
            className="gap-1.5 text-xs"
            style={{ color: showHistory ? "var(--orange)" : undefined }}
          >
            <History size={13} />
            History
          </Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        <aside
          className="w-full md:w-[440px] shrink-0 flex flex-col gap-4 px-6 py-5 md:px-7 overflow-y-auto border-b md:border-b-0 md:border-r"
          style={{ borderColor: "var(--border)" }}
        >
          {showHistory ? (
            <div className="animate-fade-up">
              <p className="text-[11px] font-semibold tracking-widest uppercase mb-3" style={{ color: "var(--text-dim)" }}>
                Past Trips
              </p>
              <TripHistory onSelect={loadHistoryTrip} loadingId={loadingHistoryId} />
            </div>
          ) : (
            <>
              <TripForm
                onSubmit={handleSubmit}
                isPending={isPending}
                initialValues={result ?? undefined}
              />

              {error && (
                <div
                  className="rounded-xl px-4 py-3 text-sm border animate-fade-up"
                  style={{
                    background: "rgba(255,23,68,0.08)",
                    borderColor: "rgba(255,23,68,0.3)",
                    color: "var(--red)",
                  }}
                >
                  {error}
                </div>
              )}

              {result && (
                <div className="animate-fade-up">
                  <TripSummary
                    totalMiles={result.route.total_miles}
                    totalDriveSecs={result.route.total_drive_secs}
                    totalDays={result.day_logs.length}
                    cycleHoursAfter={cycleAfter}
                    usedFallback={result.route.used_fallback}
                  />
                </div>
              )}
            </>
          )}
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden p-5 min-h-[400px]">
          {!result ? (
            <EmptyState />
          ) : (
            <div className="flex flex-col h-full gap-4 animate-fade-up">
              <Tabs
                value={activeTab}
                onValueChange={(v) => setActiveTab(v as "map" | "logs")}
                className="flex flex-col flex-1 min-h-0"
              >
                <TabsList className="self-start">
                  <TabsTrigger value="map">{t("results.tabs.map")}</TabsTrigger>
                  <TabsTrigger value="logs">{t("results.tabs.logs")}</TabsTrigger>
                </TabsList>

                <TabsContent value="map" className="flex-1 min-h-0">
                  <Suspense
                    fallback={
                      <div
                        className="h-full rounded-xl border flex items-center justify-center"
                        style={{ borderColor: "var(--border)", color: "var(--text-dim)", fontSize: "0.8rem" }}
                      >
                        {t("map.loadingTiles")}
                      </div>
                    }
                  >
                    <RouteMap
                      geometry={result.route.geometry}
                      events={result.events}
                      currentCoords={result.current_coords}
                      pickupCoords={result.pickup_coords}
                      dropoffCoords={result.dropoff_coords}
                    />
                  </Suspense>
                </TabsContent>

                <TabsContent value="logs" className="overflow-y-auto">
                  <LogSheet dayLogs={result.day_logs} />
                </TabsContent>
              </Tabs>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function EmptyState() {
  const { t } = useTranslation();
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center animate-fade-up">
      <div
        className="w-20 h-20 rounded-2xl flex items-center justify-center"
        style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}
      >
        <Truck size={36} style={{ color: "var(--text-dim)" }} />
      </div>
      <div>
        <p className="text-base font-medium" style={{ color: "var(--text-secondary)" }}>
          {t("results.emptyTitle")}
        </p>
        <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>
          {t("results.emptySubtitle")}
        </p>
      </div>
    </div>
  );
}
