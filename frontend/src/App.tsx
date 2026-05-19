import { lazy, Suspense, useState } from "react";
import { Truck, RotateCcw, History, Download } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { TripForm, type TripFormValues } from "@/components/TripForm/TripForm";
import { TripSummary } from "@/components/TripSummary/TripSummary";
import { TripHistory } from "@/components/TripHistory/TripHistory";
import { LogSheet } from "@/components/LogSheet/LogSheet";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";
import { useBackendWakeup } from "@/hooks/useBackendWakeup";
import { useTripStore } from "@/store/tripStore";
import { planTrip, getTripDetail, type TripPlanResponse } from "@/services/api";

const RouteMap = lazy(() =>
  import("@/components/RouteMap/RouteMap").then((m) => ({ default: m.RouteMap }))
);

export default function App() {
  const { t } = useTranslation();
  const { isWakingUp } = useBackendWakeup();
  const { activeTab, setActiveTab } = useTripStore();
  const queryClient = useQueryClient();
  const [result, setResult] = useState<TripPlanResponse | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistoryId, setLoadingHistoryId] = useState<string | null>(null);

  const planMutation = useMutation({
    mutationFn: (values: TripFormValues) =>
      planTrip({
        current_location: values.current_location,
        pickup_location: values.pickup_location,
        dropoff_location: values.dropoff_location,
        cycle_hours_used: values.cycle_hours_used,
        departure_time: values.departure_time,
      }),
    onSuccess: (data) => {
      setResult(data);
      setActiveTab("map");
      // New trip appears in history — invalidate the cached list
      void queryClient.invalidateQueries({ queryKey: ["trips"] });
    },
  });

  async function loadHistoryTrip(id: string) {
    setLoadingHistoryId(id);
    planMutation.reset();
    try {
      const data = await getTripDetail(id);
      setResult(data);
      setShowHistory(false);
      setActiveTab("map");
    } catch {
      // error handled inline in TripHistory; nothing to surface here
    } finally {
      setLoadingHistoryId(null);
    }
  }

  const cycleAfter = result
    ? parseFloat(result.day_logs.at(-1)?.recap_70hr ?? "0")
    : 0;

  const [downloadingPDF, setDownloadingPDF] = useState(false);

  async function downloadLogs() {
    if (!result) return;
    setDownloadingPDF(true);
    try {
      const [{ pdf }, { LogSheetPDF }] = await Promise.all([
        import("@react-pdf/renderer"),
        import("@/components/LogSheetPDF/LogSheetPDF"),
      ]);
      const blob = await pdf(
        <LogSheetPDF
          dayLogs={result.day_logs}
          pickupLocation={result.pickup_location}
          dropoffLocation={result.dropoff_location}
          totalMiles={result.route.total_miles}
          departureTime={result.departure_time}
          cycleHoursUsed={result.cycle_hours_used}
        />
      ).toBlob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trip-log-${result.departure_time.slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloadingPDF(false);
    }
  }

  const errorMessage = planMutation.error instanceof Error
    ? planMutation.error.message
    : planMutation.error
      ? "Something went wrong"
      : null;

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

        <div className="flex items-center gap-3">
          {isWakingUp && (
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-medium"
              style={{
                background: "rgba(255,171,0,0.1)",
                border: "1px solid rgba(255,171,0,0.25)",
                color: "var(--amber, #ffab00)",
              }}
            >
              <span
                className="block w-1.5 h-1.5 rounded-full animate-pulse"
                style={{ background: "var(--amber, #ffab00)" }}
              />
              Warming up backend…
            </div>
          )}
          <div className="flex items-center gap-1">
          {result && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setResult(null);
                planMutation.reset();
                setShowHistory(false);
                setActiveTab("map");
              }}
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
                onSubmit={(v) => planMutation.mutate(v)}
                isPending={planMutation.isPending}
                initialValues={result ?? undefined}
              />

              {errorMessage && (
                <div
                  className="rounded-xl px-4 py-3 text-sm border animate-fade-up"
                  style={{
                    background: "rgba(255,23,68,0.08)",
                    borderColor: "rgba(255,23,68,0.3)",
                    color: "var(--red)",
                  }}
                >
                  {errorMessage}
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
                <div className="flex items-center justify-between">
                  <TabsList className="self-start">
                    <TabsTrigger value="map">{t("results.tabs.map")}</TabsTrigger>
                    <TabsTrigger value="logs">{t("results.tabs.logs")}</TabsTrigger>
                  </TabsList>
                  {activeTab === "logs" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void downloadLogs()}
                      disabled={downloadingPDF}
                      className="gap-1.5 text-xs"
                    >
                      <Download size={13} />
                      {downloadingPDF ? "Generating…" : "Download PDF"}
                    </Button>
                  )}
                </div>

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
