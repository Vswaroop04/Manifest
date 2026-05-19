export interface TripPlanRequest {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  cycle_hours_used: number;
  departure_time: string; // ISO datetime e.g. "2026-05-19T08:00:00"
}

export interface TripEvent {
  id: string;
  event_type: string;
  start_time: string;
  end_time: string;
  location_label: string;
  coords: [number, number] | null;
  mile_marker: number;
  metadata: Record<string, unknown>;
}

export interface DayLog {
  day_number: number;
  date: string;
  segments: { status: string; start_min: number; end_min: number }[];
  total_driving: string;
  total_on_duty_nd: string;
  total_off_duty: string;
  total_sleeper: string;
  recap_70hr: string;
}

export interface TripPlanResponse {
  id: string;
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  cycle_hours_used: number;
  departure_time: string; // ISO datetime
  route: {
    geometry: [number, number][];
    total_miles: number;
    total_drive_secs: number;
    used_fallback: boolean;
  };
  current_coords: [number, number];
  pickup_coords: [number, number];
  dropoff_coords: [number, number];
  events: TripEvent[];
  day_logs: DayLog[];
}

export interface TripSummaryItem {
  id: string;
  status: string;
  pickup_location: string;
  dropoff_location: string;
  departure_time: string;
  cycle_hours_used: string;
  created: string;
}

function parseResponse(raw: {
  id: string;
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  cycle_hours_used: string;
  departure_time: string;
  current_coords: [number, number];
  pickup_coords: [number, number];
  dropoff_coords: [number, number];
  route: { geometry: [number, number][]; total_miles: string; total_drive_secs: number; used_fallback: boolean };
  events: TripEvent[];
  day_logs: DayLog[];
}): TripPlanResponse {
  return {
    id: raw.id,
    current_location: raw.current_location,
    pickup_location: raw.pickup_location,
    dropoff_location: raw.dropoff_location,
    cycle_hours_used: parseFloat(raw.cycle_hours_used),
    departure_time: raw.departure_time,
    current_coords: raw.current_coords,
    pickup_coords: raw.pickup_coords,
    dropoff_coords: raw.dropoff_coords,
    route: {
      geometry: raw.route.geometry,
      total_miles: parseFloat(raw.route.total_miles),
      total_drive_secs: raw.route.total_drive_secs,
      used_fallback: raw.route.used_fallback,
    },
    events: raw.events,
    day_logs: raw.day_logs,
  };
}

function getSessionToken(): string {
  const key = "manifest_session_token";
  let token = localStorage.getItem(key);
  if (!token) {
    token = crypto.randomUUID();
    localStorage.setItem(key, token);
  }
  return token;
}

function sessionHeaders(): Record<string, string> {
  return { "X-Session-Token": getSessionToken() };
}

export async function getTripList(): Promise<TripSummaryItem[]> {
  const res = await fetch("/api/trips/", { headers: sessionHeaders() });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<TripSummaryItem[]>;
}

export async function getTripDetail(id: string): Promise<TripPlanResponse> {
  const res = await fetch(`/api/trips/${id}/`, { headers: sessionHeaders() });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const raw = await res.json() as Parameters<typeof parseResponse>[0];
  return parseResponse(raw);
}

export async function planTrip(req: TripPlanRequest): Promise<TripPlanResponse> {
  const res = await fetch("/api/trips/plan/", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...sessionHeaders() },
    body: JSON.stringify(req),
  });

  const data = await res.json() as Record<string, unknown>;

  if (!res.ok) {
    const detail = (data as { detail?: string }).detail;
    throw new Error(detail ?? `API error ${res.status}`);
  }

  const raw = data as Parameters<typeof parseResponse>[0];
  return parseResponse(raw);
}
