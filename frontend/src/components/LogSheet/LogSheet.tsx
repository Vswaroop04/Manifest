import { LogSheetDay } from "./LogSheetDay";

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
  dayLogs: DayLog[];
}

export function LogSheet({ dayLogs }: Props) {
  if (dayLogs.length === 0) {
    return (
      <div
        className="flex items-center justify-center h-32 rounded-xl border"
        style={{ borderColor: "var(--border)", color: "var(--text-dim)", fontSize: "0.8rem", fontFamily: "var(--font-mono)" }}
      >
        No log data
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {dayLogs.map((log, i) => (
        <div
          key={log.day_number}
          className="animate-fade-up"
          style={{ animationDelay: `${i * 0.08}s` }}
        >
          <LogSheetDay log={log} />
        </div>
      ))}
    </div>
  );
}
