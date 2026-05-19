import {
  Document,
  Font,
  Page,
  StyleSheet,
  Svg,
  Text,
  View,
  Line,
  Rect,
  G,
} from "@react-pdf/renderer";

Font.registerHyphenationCallback((w) => [w]);

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

interface Props {
  dayLogs: DayLog[];
  pickupLocation: string;
  dropoffLocation: string;
  totalMiles: number;
  departureTime: string;
  cycleHoursUsed: number;
}

// ── PDF page constants (points, letter size 612×792) ────────────────────────
const PAGE_W = 612;
const MARGIN = 36;
const CONTENT_W = PAGE_W - MARGIN * 2;

// Grid
const LABEL_COL = 72;   // row label column width
const TOTALS_COL = 36;  // right-side totals column
const GRID_W = CONTENT_W - LABEL_COL - TOTALS_COL; // ≈ 396pt
const PX_PER_MIN = GRID_W / 1440;
const ROW_H = 22;
const ROWS = [
  { label: "1. Off Duty",       key: "off_duty",    fill: "#5c6494", opacity: 0.9 },
  { label: "2. Sleeper Berth",  key: "sleeper",     fill: "#0097a7", opacity: 0.9 },
  { label: "3. Driving",        key: "driving",     fill: "#1b7a4a", opacity: 0.9 },
  { label: "4. On Duty (ND)",   key: "on_duty_nd",  fill: "#b37a00", opacity: 0.9 },
] as const;

const HOURS = Array.from({ length: 25 }, (_, i) => i);

// ── helpers ──────────────────────────────────────────────────────────────────
function formatDate(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return {
    month: String(d.getMonth() + 1).padStart(2, "0"),
    day:   String(d.getDate()).padStart(2, "0"),
    year:  String(d.getFullYear()),
    label: d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" }),
  };
}

function decToHM(val: string): string {
  const n = parseFloat(val);
  const h = Math.floor(n);
  const m = Math.round((n - h) * 60);
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function hourLabel(h: number): string {
  if (h === 0 || h === 24) return "M";
  if (h === 12) return "N";
  return h < 12 ? String(h) : String(h - 12);
}

// ── sub-components ───────────────────────────────────────────────────────────
const s = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 7,
    color: "#111",
    paddingTop: MARGIN,
    paddingBottom: MARGIN,
    paddingHorizontal: MARGIN,
    backgroundColor: "#fff",
  },
  title: { fontSize: 13, fontFamily: "Helvetica-Bold", marginBottom: 2 },
  subtitle: { fontSize: 7, color: "#555", marginBottom: 8 },
  row: { flexDirection: "row", alignItems: "flex-start" },
  col: { flexDirection: "column" },
  bold: { fontFamily: "Helvetica-Bold" },
  fieldLabel: { fontSize: 6, color: "#555", marginBottom: 1 },
  fieldBox: {
    border: "0.5pt solid #aaa",
    padding: "3 5",
    marginBottom: 4,
    minHeight: 14,
  },
  hrLine: { borderBottom: "0.5pt solid #aaa", marginVertical: 5 },
  sectionLabel: { fontSize: 6, color: "#777", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 2 },
  gridLabel: { fontSize: 6.5, fontFamily: "Helvetica-Bold" },
  totalBox: { borderLeft: "0.5pt solid #aaa", textAlign: "center", paddingLeft: 2, fontSize: 6.5 },
});

function HeaderBlock({ log, pickupLocation, dropoffLocation, totalMiles, dayMiles, cycleHoursUsed }: {
  log: DayLog;
  pickupLocation: string;
  dropoffLocation: string;
  totalMiles: number;
  dayMiles: number;
  cycleHoursUsed: number;
}) {
  const d = formatDate(log.date);
  return (
    <View>
      {/* Title row */}
      <View style={[s.row, { justifyContent: "space-between", marginBottom: 4 }]}>
        <View>
          <Text style={s.title}>Driver's Daily Log</Text>
          <Text style={s.subtitle}>(24 hours){"  "}For use by motor carriers subject to Part 395</Text>
        </View>
        <View style={{ alignItems: "flex-end" }}>
          <View style={[s.row, { gap: 4 }]}>
            <View style={{ alignItems: "center" }}>
              <Text style={s.fieldLabel}>Month</Text>
              <Text style={[s.fieldBox, { width: 28, textAlign: "center" }]}>{d.month}</Text>
            </View>
            <View style={{ alignItems: "center" }}>
              <Text style={s.fieldLabel}>Day</Text>
              <Text style={[s.fieldBox, { width: 22, textAlign: "center" }]}>{d.day}</Text>
            </View>
            <View style={{ alignItems: "center" }}>
              <Text style={s.fieldLabel}>Year</Text>
              <Text style={[s.fieldBox, { width: 32, textAlign: "center" }]}>{d.year}</Text>
            </View>
          </View>
          <Text style={{ fontSize: 6, color: "#555", textAlign: "right" }}>
            Day {log.day_number} of trip
          </Text>
        </View>
      </View>

      {/* From / To */}
      <View style={[s.row, { gap: 8, marginBottom: 4 }]}>
        <View style={{ flex: 1 }}>
          <Text style={s.fieldLabel}>From (origin)</Text>
          <Text style={s.fieldBox}>{pickupLocation}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.fieldLabel}>To (destination)</Text>
          <Text style={s.fieldBox}>{dropoffLocation}</Text>
        </View>
      </View>

      {/* Stats row */}
      <View style={[s.row, { gap: 8, marginBottom: 6 }]}>
        <View style={{ width: 80 }}>
          <Text style={s.fieldLabel}>Total Miles Driving Today</Text>
          <Text style={s.fieldBox}>{dayMiles.toFixed(1)}</Text>
        </View>
        <View style={{ width: 80 }}>
          <Text style={s.fieldLabel}>Total Trip Miles</Text>
          <Text style={s.fieldBox}>{totalMiles.toFixed(1)}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.fieldLabel}>Cycle Hours Used (start of trip)</Text>
          <Text style={s.fieldBox}>{cycleHoursUsed.toFixed(1)} hr used / {(70 - cycleHoursUsed).toFixed(1)} hr available</Text>
        </View>
      </View>

      <View style={s.hrLine} />
    </View>
  );
}

function GridBlock({ log }: { log: DayLog }) {
  const gridH = ROW_H * ROWS.length;
  const svgH = gridH + 24; // + top labels

  return (
    <View style={{ marginBottom: 6 }}>
      <Text style={[s.sectionLabel, { marginBottom: 3 }]}>Hours of Service — 24-Hour Grid (midnight to midnight)</Text>
      <Svg width={CONTENT_W} height={svgH}>
        {/* Hour column labels */}
        {HOURS.map((h) => (
          <G key={h}>
            <Text
              x={LABEL_COL + h * PX_PER_MIN * 60}
              y={10}
              style={{ fontSize: 5.5, textAnchor: "middle", fill: "#333", fontFamily: "Helvetica" }}
            >
              {hourLabel(h)}
            </Text>
          </G>
        ))}

        {/* Row backgrounds and labels */}
        {ROWS.map((row, ri) => {
          const rowY = 14 + ri * ROW_H;
          return (
            <G key={row.key}>
              {/* Label cell */}
              <Rect x={0} y={rowY} width={LABEL_COL} height={ROW_H} fill="#f5f5f5" stroke="#ccc" strokeWidth={0.5} />
              <Text x={LABEL_COL - 4} y={rowY + ROW_H / 2 + 2} style={{ fontSize: 6, textAnchor: "end", fill: "#333", fontFamily: "Helvetica-Bold" }}>
                {row.label}
              </Text>

              {/* Grid background */}
              <Rect x={LABEL_COL} y={rowY} width={GRID_W} height={ROW_H} fill="#fafafa" stroke="#ccc" strokeWidth={0.5} />

              {/* Totals cell */}
              <Rect x={LABEL_COL + GRID_W} y={rowY} width={TOTALS_COL} height={ROW_H} fill="#f0f0f0" stroke="#ccc" strokeWidth={0.5} />
            </G>
          );
        })}

        {/* Vertical hour lines */}
        {HOURS.map((h) => (
          <Line
            key={h}
            x1={LABEL_COL + h * PX_PER_MIN * 60}
            y1={14}
            x2={LABEL_COL + h * PX_PER_MIN * 60}
            y2={14 + gridH}
            stroke={h % 6 === 0 ? "#999" : h % 3 === 0 ? "#ccc" : "#e0e0e0"}
            strokeWidth={h % 6 === 0 ? 0.8 : 0.4}
          />
        ))}

        {/* 15-min tick marks */}
        {Array.from({ length: 24 * 3 }, (_, i) => {
          const min = (i + 1) * 15;
          if (min % 60 === 0) return null;
          const x = LABEL_COL + min * PX_PER_MIN;
          return (
            <Line key={i} x1={x} y1={14} x2={x} y2={14 + 4} stroke="#ccc" strokeWidth={0.3} />
          );
        })}

        {/* Status fill bars */}
        {log.segments.map((seg, si) => {
          const rowDef = ROWS.find((r) => r.key === seg.status);
          if (!rowDef) return null;
          const ri = ROWS.indexOf(rowDef);
          const rowY = 14 + ri * ROW_H;
          const x = LABEL_COL + seg.start_min * PX_PER_MIN;
          const w = (seg.end_min - seg.start_min) * PX_PER_MIN;
          if (w <= 0) return null;
          return (
            <Rect
              key={si}
              x={x}
              y={rowY + 3}
              width={w}
              height={ROW_H - 6}
              fill={rowDef.fill}
              opacity={rowDef.opacity}
              rx={1}
            />
          );
        })}

        {/* Totals values */}
        {ROWS.map((row, ri) => {
          const rowY = 14 + ri * ROW_H;
          const totalKey = row.key === "off_duty" ? "total_off_duty"
            : row.key === "sleeper" ? "total_sleeper"
            : row.key === "driving" ? "total_driving"
            : "total_on_duty_nd";
          const val = decToHM(log[totalKey as keyof DayLog] as string);
          return (
            <Text
              key={row.key}
              x={LABEL_COL + GRID_W + TOTALS_COL / 2}
              y={rowY + ROW_H / 2 + 2}
              style={{ fontSize: 6, textAnchor: "middle", fill: "#333", fontFamily: "Helvetica" }}
            >
              {val}
            </Text>
          );
        })}

        {/* "Total Hrs" header for totals column */}
        <Text
          x={LABEL_COL + GRID_W + TOTALS_COL / 2}
          y={10}
          style={{ fontSize: 5, textAnchor: "middle", fill: "#555", fontFamily: "Helvetica" }}
        >
          Total
        </Text>
      </Svg>
    </View>
  );
}

function RecapBlock({ log }: { log: DayLog }) {
  const onDutyToday = parseFloat(log.total_driving) + parseFloat(log.total_on_duty_nd);
  const avail70 = Math.max(0, 70 - parseFloat(log.recap_70hr));

  return (
    <View style={{ marginTop: 6 }}>
      <Text style={s.sectionLabel}>Recap — 70 Hour / 8 Day Cycle</Text>
      <View style={[s.row, { gap: 12, marginTop: 4 }]}>
        <View style={{ width: 110 }}>
          <Text style={s.fieldLabel}>A. On Duty hours today (rows 3 + 4)</Text>
          <Text style={s.fieldBox}>{onDutyToday.toFixed(2)} hr</Text>
        </View>
        <View style={{ width: 130 }}>
          <Text style={s.fieldLabel}>B. Total on-duty hrs last 8 days (incl. today)</Text>
          <Text style={s.fieldBox}>{parseFloat(log.recap_70hr).toFixed(2)} hr</Text>
        </View>
        <View style={{ width: 130 }}>
          <Text style={s.fieldLabel}>C. Total hours available tomorrow (70 − B)</Text>
          <Text style={s.fieldBox}>{avail70.toFixed(2)} hr</Text>
        </View>
      </View>
    </View>
  );
}

function RemarksBlock() {
  return (
    <View style={{ marginTop: 8 }}>
      <Text style={s.sectionLabel}>Remarks</Text>
      <View style={{ border: "0.5pt solid #aaa", height: 40, marginTop: 2 }} />
    </View>
  );
}

// ── Document ─────────────────────────────────────────────────────────────────
export function LogSheetPDF({
  dayLogs,
  pickupLocation,
  dropoffLocation,
  totalMiles,
  departureTime: _departureTime,
  cycleHoursUsed,
}: Props) {
  const drivingMilesPerDay = totalMiles / Math.max(dayLogs.length, 1);

  return (
    <Document
      title="Driver's Daily Log"
      author="ELD Trip Planner"
      creator="ELD Trip Planner"
    >
      {dayLogs.map((log) => (
        <Page key={log.day_number} size="LETTER" style={s.page}>
          <HeaderBlock
            log={log}
            pickupLocation={pickupLocation}
            dropoffLocation={dropoffLocation}
            totalMiles={totalMiles}
            dayMiles={drivingMilesPerDay}
            cycleHoursUsed={cycleHoursUsed}
          />
          <GridBlock log={log} />
          <RecapBlock log={log} />
          <RemarksBlock />

          {/* Legend */}
          <View style={[s.row, { gap: 10, marginTop: 8 }]}>
            {ROWS.map((r) => (
              <View key={r.key} style={[s.row, { alignItems: "center", gap: 3 }]}>
                <Svg width={10} height={10}>
                  <Rect x={0} y={0} width={10} height={10} fill={r.fill} opacity={r.opacity} rx={1} />
                </Svg>
                <Text style={{ fontSize: 6, color: "#444" }}>{r.label}</Text>
              </View>
            ))}
          </View>

          {/* Footer */}
          <View style={[s.hrLine, { marginTop: 8 }]} />
          <Text style={{ fontSize: 6, color: "#888", textAlign: "center" }}>
            Generated by ELD Trip Planner · FMCSA 49 CFR Part 395 · Page {log.day_number} of {dayLogs.length}
          </Text>
        </Page>
      ))}
    </Document>
  );
}
