import { AgentDayVm } from "../vm/agentPlanning.vm";
import { buildTimeWindows, formatWindows } from "@/features/planning-agent/utils/month.summary";
import { AgentMiniGantt } from "./AgentMiniGantt";
import { Badge } from "@/components/ui/badge";

function dayNumber(iso: string) {
  return String(Number(iso.slice(8, 10)));
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
    <Badge
      variant="outline"
      className="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium"
    >
      <span className="inline-flex items-center gap-1.5">
        <span
          className="inline-flex h-2 w-2 rounded-full"
          style={{ backgroundColor: dayTypeDotColor(dayType) }}
        />
        <span>{label}</span>
      </span>
    </Badge>
  );
}

export function AgentDayCell(props: {
  day: AgentDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  onSelect: () => void;
  posteNameById: Map<number, string>;
}) {
  const { day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect } = props;

  const windows = buildTimeWindows(day.segments, 60);
  const timeText = formatWindows(windows, 2);

  const ringClass = isSelected
    ? "ring-2 ring-[color:var(--app-ring)]"
    : isInSelectedWeek
    ? "ring-1 ring-[color:var(--app-border)]"
    : "";

  const ariaLabel = [
    `Jour ${dayNumber(day.day_date)}`,
    `Type: ${dayTypeLabel(day.day_type)}`,
    timeText ? `Horaires: ${timeText}` : null,
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
      aria-label={ariaLabel}
      className={[
        "w-full rounded-xl border p-2 text-left transition",
        "border-[color:var(--app-border)] bg-[color:var(--app-surface)] hover:bg-[color:var(--app-soft)]",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring)]",
        "hover:-translate-y-[1px] hover:shadow-sm",
        isOutsideMonth ? "opacity-50" : "",
        ringClass,
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
          <AgentMiniGantt
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
