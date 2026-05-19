import { useEffect, useState } from "react";
import { API_BASE } from "@/services/api";

type WakeupStatus = "pending" | "up" | "error";

export function useBackendWakeup() {
  const [status, setStatus] = useState<WakeupStatus>("pending");
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    let cancelled = false;

    // Only show the banner if the backend takes more than 800ms — fast responses
    // don't need any UI noise.
    const slowTimer = setTimeout(() => {
      if (!cancelled) setSlow(true);
    }, 800);

    fetch(`${API_BASE}/api/health/`)
      .then((r) => (r.ok ? "up" : "error") as WakeupStatus)
      .catch(() => "error" as WakeupStatus)
      .then((result) => {
        if (!cancelled) {
          clearTimeout(slowTimer);
          setSlow(false);
          setStatus(result);
        }
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, []);

  return {
    isWakingUp: status === "pending" && slow,
    isUp: status === "up",
  };
}
