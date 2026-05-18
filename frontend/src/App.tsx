import { useState } from "react";
import { Truck, RotateCcw } from "lucide-react";
import { TripForm, type TripFormValues } from "@/components/TripForm/TripForm";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";

export default function App() {
  const { t } = useTranslation();
  const [isPending, setIsPending] = useState(false);
  const [hasResult, setHasResult] = useState(false);

  async function handleSubmit(values: TripFormValues) {
    setIsPending(true);
    console.log("Trip request:", values);
    await new Promise((r) => setTimeout(r, 1200));
    setIsPending(false);
    setHasResult(true);
  }

  return (
    <div className="flex flex-col h-full">
      <header
        className="flex items-center justify-between px-6 py-3 border-b shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg"
            style={{ background: "var(--orange-dim)", border: "1px solid var(--orange)" }}
          >
            <Truck size={16} style={{ color: "var(--orange)" }} />
          </div>
          <div>
            <span
              className="text-xl tracking-widest"
              style={{ fontFamily: "var(--font-display)", color: "var(--text)" }}
            >
              {t("app.name")}
            </span>
            <span
              className="ml-2 text-xs"
              style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}
            >
              {t("app.tagline")}
            </span>
          </div>
        </div>

        {hasResult && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setHasResult(false)}
            className="gap-1.5 text-xs"
          >
            <RotateCcw size={13} />
            {t("nav.newTrip")}
          </Button>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside
          className="w-[380px] shrink-0 flex flex-col gap-4 p-5 overflow-y-auto border-r"
          style={{ borderColor: "var(--border)" }}
        >
          <TripForm onSubmit={handleSubmit} isPending={isPending} />
        </aside>

        <main className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
          {!hasResult ? (
            <EmptyState />
          ) : (
            <ResultsPlaceholder />
          )}
        </main>
      </div>
    </div>
  );
}

function EmptyState() {
  const { t } = useTranslation();
  return (
    <div
      className="flex flex-col items-center gap-4 text-center animate-fade-up"
      style={{ animationDelay: "0.1s" }}
    >
      <div
        className="w-20 h-20 rounded-2xl flex items-center justify-center"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border)",
        }}
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

function ResultsPlaceholder() {
  return (
    <div
      className="w-full h-full flex items-center justify-center rounded-xl border animate-fade-up"
      style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
    >
      <p style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
        Map + Log Sheets loading…
      </p>
    </div>
  );
}
