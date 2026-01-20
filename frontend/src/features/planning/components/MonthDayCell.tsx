import type { AgentDayVm } from "@/features/planning/vm/planning.vm";
import { buildTimeWindows, formatWindows } from "@/features/planning/utils/month.summary";
import { MonthMiniGantt } from "@/features/planning/components/MonthMiniGantt";

function dayNumber(iso: string) {
  return iso.slice(8, 10);
}

function dayTypeLabel(dayType: string) {
  return dayType === "working"
    ? "Travail"
    : dayType === "rest"
    ? "Repos"
    : dayType === "absence"
    ? "Absence"
    : dayType === "unknown"
    ? "—"
    : dayType;
}

function dayTypeDotColor(dayType: string) {
  if (dayType === "working") return "var(--palaj-l)";
  if (dayType === "absence") return "var(--palaj-a)";
  if (dayType === "rest") return "var(--app-muted)";
  return "var(--app-muted)";
}

function DayTypeBadge({ dayType }: { dayType: string }) {
  const label = dayTypeLabel(dayType);

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-2 py-0.5 text-[11px] font-medium text-[color:var(--app-muted)]">
      <span
        className="inline-flex h-2 w-2 rounded-full"
        style={{ backgroundColor: dayTypeDotColor(dayType) }}
      />
      <span className="text-[color:var(--app-text)]">{label}</span>
    </span>
  );
}

export function MonthDayCell(props: {
  day: AgentDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  onSelect: () => void;
  posteNameById: Map<number, string>;
}) {
  const { day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect } = props;

  // résumé intelligent par "fenêtres"
  const windows = buildTimeWindows(day.segments, 60);
  const timeText = formatWindows(windows, 2);

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
      className={[
        "w-full text-left rounded-xl border p-2 transition",
        "border-[color:var(--app-border)] bg-[color:var(--app-surface)]",
        "hover:bg-[color:var(--app-soft)] hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900/10",
        isOutsideMonth ? "opacity-50" : "",
        isInSelectedWeek ? "ring-1 ring-[color:var(--app-border)] ring-inset" : "",
        isSelected ? "ring-2 ring-[color:var(--app-text)]/40 ring-inset" : "",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm font-semibold text-[color:var(--app-text)] tabular-nums">
          {dayNumber(day.day_date)}
        </div>
        <DayTypeBadge dayType={day.day_type} />
      </div>

      <div className="mt-1 truncate text-[12px] text-[color:var(--app-muted)]">
        {timeText}
      </div>

      {day.segments.length > 0 ? (
        <div className="mt-2">
          <MonthMiniGantt
            segments={day.segments}
            dayStart="00:00:00"
            dayEnd="24:00:00"
            maxLanes={2}
          />
        </div>
      ) : null}
    </button>
  );
}
