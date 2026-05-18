import { lazy, Suspense, useState } from "react";
import { Truck, RotateCcw } from "lucide-react";
import { TripForm, type TripFormValues } from "@/components/TripForm/TripForm";
import { TripSummary } from "@/components/TripSummary/TripSummary";
import { LogSheet } from "@/components/LogSheet/LogSheet";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";
import { useTripStore } from "@/store/tripStore";

const RouteMap = lazy(() =>
  import("@/components/RouteMap/RouteMap").then((m) => ({ default: m.RouteMap }))
);

const MOCK_RESULT = {
  route: {
    geometry: [
      [41.8781, -87.6298], [41.82, -89.0], [41.74, -90.3],
      [41.67, -91.52], [41.59, -93.0], [41.5868, -93.625],
      [41.55, -94.8], [41.26, -95.9], [40.59, -100.77],
      [39.9, -103.6], [39.7392, -104.9903],
    ] as [number, number][],
    total_miles: 1358.4,
    total_drive_secs: 88200,
    used_fallback: false,
  },
  current_coords: [41.8781, -87.6298] as [number, number],
  pickup_coords: [41.5868, -93.625] as [number, number],
  dropoff_coords: [39.7392, -104.9903] as [number, number],
  events: [
    { id: "ev-03", event_type: "break",   start_time: "2026-05-20T13:30:00Z", end_time: "2026-05-20T14:00:00Z", location_label: "Rest Area I-80, IA",  coords: [41.67, -91.52] as [number, number], mile_marker: 302 },
    { id: "ev-05", event_type: "pickup",  start_time: "2026-05-20T17:30:00Z", end_time: "2026-05-20T18:30:00Z", location_label: "Des Moines, IA",       coords: [41.5868, -93.625] as [number, number], mile_marker: 494 },
    { id: "ev-07", event_type: "rest",    start_time: "2026-05-20T20:30:00Z", end_time: "2026-05-21T06:30:00Z", location_label: "Council Bluffs, IA",   coords: [41.26, -95.9] as [number, number], mile_marker: 604 },
    { id: "ev-09", event_type: "fuel",    start_time: "2026-05-21T11:30:00Z", end_time: "2026-05-21T12:00:00Z", location_label: "North Platte, NE",     coords: [40.59, -100.77] as [number, number], mile_marker: 879 },
    { id: "ev-11", event_type: "dropoff", start_time: "2026-05-21T16:30:00Z", end_time: "2026-05-21T17:30:00Z", location_label: "Denver, CO",           coords: [39.7392, -104.9903] as [number, number], mile_marker: 1358 },
  ],
  day_logs: [
    {
      day_number: 1, date: "2026-05-20",
      segments: [
        { status: "off_duty",   start_min: 0,    end_min: 480  },
        { status: "driving",    start_min: 480,  end_min: 810  },
        { status: "off_duty",   start_min: 810,  end_min: 840  },
        { status: "driving",    start_min: 840,  end_min: 1050 },
        { status: "on_duty_nd", start_min: 1050, end_min: 1110 },
        { status: "driving",    start_min: 1110, end_min: 1230 },
        { status: "off_duty",   start_min: 1230, end_min: 1440 },
      ],
      total_driving: "11.00", total_on_duty_nd: "1.00",
      total_off_duty: "12.00", total_sleeper: "0.00", recap_70hr: "12.00",
    },
    {
      day_number: 2, date: "2026-05-21",
      segments: [
        { status: "off_duty",   start_min: 0,   end_min: 390  },
        { status: "driving",    start_min: 390, end_min: 690  },
        { status: "on_duty_nd", start_min: 690, end_min: 720  },
        { status: "driving",    start_min: 720, end_min: 990  },
        { status: "on_duty_nd", start_min: 990, end_min: 1050 },
        { status: "off_duty",   start_min: 1050, end_min: 1440 },
      ],
      total_driving: "9.50", total_on_duty_nd: "1.50",
      total_off_duty: "13.00", total_sleeper: "0.00", recap_70hr: "23.50",
    },
  ],
};

export default function App() {
  const { t } = useTranslation();
  const { activeTab, setActiveTab } = useTripStore();
  const [isPending, setIsPending] = useState(false);
  const [result, setResult] = useState<typeof MOCK_RESULT | null>(null);

  async function handleSubmit(values: TripFormValues) {
    setIsPending(true);
    console.log("Trip request:", values);
    await new Promise((r) => setTimeout(r, 1000));
    setIsPending(false);
    setResult(MOCK_RESULT);
  }

  const cycleAfter =
    result
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

        {result && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setResult(null); setActiveTab("map"); }}
            className="gap-1.5 text-xs"
          >
            <RotateCcw size={13} />
            {t("nav.newTrip")}
          </Button>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        <aside
          className="w-full md:w-[420px] shrink-0 flex flex-col gap-4 px-4 py-5 md:px-6 overflow-y-auto border-b md:border-b-0 md:border-r"
          style={{ borderColor: "var(--border)" }}
        >
          <TripForm onSubmit={handleSubmit} isPending={isPending} />

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
