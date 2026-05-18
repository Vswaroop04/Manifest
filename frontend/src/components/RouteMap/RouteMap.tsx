import { useEffect } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function makeIcon(color: string, size: number = 10) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${color};border:2px solid rgba(0,0,0,0.5);
      box-shadow:0 0 6px ${color}88;
    "></div>`,
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 4)],
  });
}

const EVENT_COLORS: Record<string, string> = {
  pickup: "var(--orange)",
  dropoff: "var(--orange)",
  rest: "var(--cyan)",
  break: "var(--amber)",
  fuel: "var(--amber)",
  off_duty: "#2a3060",
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric", minute: "2-digit", hour12: true,
  });
}

function formatDuration(start: string, end: string): string {
  const mins = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 60000);
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

interface TripEvent {
  id: string;
  event_type: string;
  start_time: string;
  end_time: string;
  location_label: string;
  coords: [number, number] | null;
  mile_marker: number;
}

interface Props {
  geometry: [number, number][];
  events: TripEvent[];
  currentCoords: [number, number];
  pickupCoords: [number, number];
  dropoffCoords: [number, number];
}

function FitBounds({ geometry }: { geometry: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (geometry.length > 1) {
      map.fitBounds(L.latLngBounds(geometry), { padding: [40, 40] });
    }
  }, [map, geometry]);
  return null;
}

export function RouteMap({ geometry, events, currentCoords, pickupCoords, dropoffCoords }: Props) {
  const center: [number, number] = geometry.length > 0 ? geometry[0] : [39.5, -98.35];

  const stopEvents = events.filter(
    (e) => e.coords && e.event_type !== "driving" && e.event_type !== "off_duty"
  );

  return (
    <div
      className="rounded-xl overflow-hidden border"
      style={{ borderColor: "var(--border)", height: "100%", minHeight: "380px" }}
    >
      <MapContainer
        center={center}
        zoom={5}
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://openstreetmap.org">OSM</a>'
        />
        <FitBounds geometry={geometry} />

        {/* Route polyline */}
        {geometry.length > 1 && (
          <Polyline
            positions={geometry}
            color="var(--cyan)"
            weight={3}
            opacity={0.85}
          />
        )}

        {/* Current location */}
        <Marker position={currentCoords} icon={makeIcon("#00e5ff", 12)}>
          <Popup>
            <div style={{ fontFamily: "var(--font-body)", fontSize: "13px" }}>
              <strong style={{ color: "var(--cyan)" }}>Current Location</strong>
            </div>
          </Popup>
        </Marker>

        {/* Pickup */}
        <Marker position={pickupCoords} icon={makeIcon("var(--orange)", 14)}>
          <Popup>
            <div style={{ fontFamily: "var(--font-body)", fontSize: "13px" }}>
              <strong style={{ color: "var(--orange)" }}>Pickup</strong>
            </div>
          </Popup>
        </Marker>

        {/* Dropoff */}
        <Marker position={dropoffCoords} icon={makeIcon("var(--green)", 14)}>
          <Popup>
            <div style={{ fontFamily: "var(--font-body)", fontSize: "13px" }}>
              <strong style={{ color: "var(--green)" }}>Dropoff</strong>
            </div>
          </Popup>
        </Marker>

        {/* Stop markers */}
        {stopEvents.map((ev) => (
          <Marker
            key={ev.id}
            position={ev.coords!}
            icon={makeIcon(EVENT_COLORS[ev.event_type] ?? "var(--text-secondary)", 10)}
          >
            <Popup>
              <div style={{ fontFamily: "var(--font-body)", fontSize: "13px", minWidth: "160px" }}>
                <p style={{ fontWeight: 600, marginBottom: "6px", color: EVENT_COLORS[ev.event_type] ?? "inherit" }}>
                  {ev.location_label}
                </p>
                <p style={{ color: "var(--text-secondary)", fontSize: "11px" }}>
                  Arrive {formatTime(ev.start_time)}
                </p>
                <p style={{ color: "var(--text-secondary)", fontSize: "11px" }}>
                  Depart {formatTime(ev.end_time)}
                </p>
                <p style={{ color: "var(--text-secondary)", fontSize: "11px" }}>
                  Duration {formatDuration(ev.start_time, ev.end_time)}
                </p>
                <p style={{ color: "var(--text-dim)", fontSize: "11px" }}>
                  Mile {ev.mile_marker}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
