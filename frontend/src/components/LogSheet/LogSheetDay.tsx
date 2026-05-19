interface Segment {
  status: string;
  start_min: number;
  end_min: number;
}

interface DayLog {
  day_number: number;
  date: string;
  segments: Segment[];
  total_driving: string;
  total_on_duty_nd: string;
  total_off_duty: string;
  total_sleeper: string;
  recap_70hr: string;
}

interface Props {
  log: DayLog;
}

const ROWS = [
  { label: "Off Duty",    key: "off_duty",    y: 44 },
  { label: "Sleeper",     key: "sleeper",     y: 84 },
  { label: "Driving",     key: "driving",     y: 124 },
  { label: "On Duty ND",  key: "on_duty_nd",  y: 164 },
] as const;

const BAR_H = 32;
const LABEL_W = 88;
const GRID_W = 1440;
const SVG_W = LABEL_W + GRID_W;
const SVG_H = 230;
const GRID_TOP = 28;

function segmentFill(status: string): string {
  switch (status) {
    case "driving":    return "var(--green)";
    case "on_duty_nd": return "var(--amber)";
    case "sleeper":    return "var(--cyan)";
    case "off_duty":   return "#4a5280";
    default:           return "#4a5280";
  }
}

function segmentOpacity(status: string): number {
  switch (status) {
    case "driving":    return 0.85;
    case "on_duty_nd": return 0.85;
    case "sleeper":    return 0.75;
    case "off_duty":   return 0.45;
    default:           return 0.45;
  }
}

function formatDecimal(val: string): string {
  const n = parseFloat(val);
  const h = Math.floor(n);
  const m = Math.round((n - h) * 60);
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h${m}m`;
}

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric",
  });
}

export function LogSheetDay({ log }: Props) {
  const hours = Array.from({ length: 25 }, (_, i) => i);

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
    >
      <div
        className="flex items-center justify-between px-4 py-2.5 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-3">
          <span
            className="text-xs font-semibold px-2 py-0.5 rounded"
            style={{
              background: "var(--orange-dim)",
              color: "var(--orange)",
              fontFamily: "var(--font-mono)",
              border: "1px solid rgba(255,87,34,0.3)",
            }}
          >
            DAY {log.day_number}
          </span>
          <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
            {formatDate(log.date)}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs" style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
          <span style={{ color: "var(--green)" }}>▸ {formatDecimal(log.total_driving)}</span>
          <span style={{ color: "var(--amber)" }}>◈ {formatDecimal(log.total_on_duty_nd)}</span>
          <span style={{ color: "var(--cyan)" }}>◗ {formatDecimal(log.total_sleeper)}</span>
          <span style={{ color: "#4a5280" }}>○ {formatDecimal(log.total_off_duty)}</span>
          <span
            className="px-2 py-0.5 rounded"
            style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}
          >
            70hr: {formatDecimal(log.recap_70hr)}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          style={{ width: "100%", minWidth: "600px", display: "block" }}
          aria-label={`Log sheet day ${log.day_number}`}
        >
          <rect width={SVG_W} height={SVG_H} fill="var(--bg-card)" />

          {/* Hour column labels */}
          {hours.map((h) => (
            <text
              key={h}
              x={LABEL_W + h * 60}
              y={18}
              textAnchor="middle"
              fill="var(--text-dim)"
              fontSize={9}
              fontFamily="var(--font-mono)"
            >
              {h === 0 ? "M" : h === 12 ? "N" : h === 24 ? "M" : h < 12 ? h : h - 12}
            </text>
          ))}

          {/* AM / PM labels */}
          <text x={LABEL_W + 6 * 60} y={10} textAnchor="middle" fill="var(--text-dim)" fontSize={7} fontFamily="var(--font-mono)">AM</text>
          <text x={LABEL_W + 18 * 60} y={10} textAnchor="middle" fill="var(--text-dim)" fontSize={7} fontFamily="var(--font-mono)">PM</text>

          {/* Row backgrounds + labels */}
          {ROWS.map((row) => (
            <g key={row.key}>
              <rect
                x={0}
                y={row.y}
                width={LABEL_W}
                height={BAR_H}
                fill="var(--bg-elevated)"
              />
              <text
                x={LABEL_W - 6}
                y={row.y + BAR_H / 2 + 4}
                textAnchor="end"
                fill="var(--text-secondary)"
                fontSize={9}
                fontFamily="var(--font-body)"
              >
                {row.label}
              </text>
              <rect
                x={LABEL_W}
                y={row.y}
                width={GRID_W}
                height={BAR_H}
                fill="var(--bg-elevated)"
                opacity={0.35}
              />
            </g>
          ))}

          {/* Vertical hour grid lines */}
          {hours.map((h) => (
            <line
              key={h}
              x1={LABEL_W + h * 60}
              y1={GRID_TOP}
              x2={LABEL_W + h * 60}
              y2={SVG_H - 18}
              stroke={h % 6 === 0 ? "var(--border-bright)" : "var(--border)"}
              strokeWidth={h % 6 === 0 ? 1 : 0.5}
            />
          ))}

          {/* Half-hour tick marks */}
          {Array.from({ length: 24 }, (_, h) => (
            <line
              key={h}
              x1={LABEL_W + h * 60 + 30}
              y1={GRID_TOP}
              x2={LABEL_W + h * 60 + 30}
              y2={GRID_TOP + 6}
              stroke="var(--border)"
              strokeWidth={0.5}
            />
          ))}

          {/* Horizontal row dividers */}
          {ROWS.map((row) => (
            <line
              key={row.key}
              x1={LABEL_W}
              y1={row.y}
              x2={SVG_W}
              y2={row.y}
              stroke="var(--border)"
              strokeWidth={0.5}
            />
          ))}
          <line x1={LABEL_W} y1={ROWS[ROWS.length - 1].y + BAR_H} x2={SVG_W} y2={ROWS[ROWS.length - 1].y + BAR_H} stroke="var(--border)" strokeWidth={0.5} />

          {/* Status bars */}
          {log.segments.map((seg, i) => {
            const row = ROWS.find((r) => r.key === seg.status);
            if (!row) return null;
            const x = LABEL_W + seg.start_min;
            const w = seg.end_min - seg.start_min;
            if (w <= 0) return null;
            return (
              <rect
                key={i}
                x={x}
                y={row.y + 4}
                width={w}
                height={BAR_H - 8}
                fill={segmentFill(seg.status)}
                rx={2}
                opacity={segmentOpacity(seg.status)}
              />
            );
          })}

          {/* Midnight line */}
          <line x1={LABEL_W} y1={GRID_TOP} x2={LABEL_W} y2={SVG_H - 18} stroke="var(--border-bright)" strokeWidth={1} />

          {/* Time labels at bottom */}
          {[0, 6, 12, 18, 24].map((h) => (
            <text
              key={h}
              x={LABEL_W + h * 60}
              y={SVG_H - 4}
              textAnchor="middle"
              fill="var(--text-dim)"
              fontSize={8}
              fontFamily="var(--font-mono)"
            >
              {h === 0 || h === 24 ? "12:00" : h < 12 ? `${h}:00` : h === 12 ? "12:00" : `${h - 12}:00`}
            </text>
          ))}
        </svg>
      </div>
    </div>
  );
}
