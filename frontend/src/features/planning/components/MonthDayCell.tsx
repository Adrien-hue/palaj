import type { AgentDayVm } from "@/features/planning/vm/planning.vm";
import { buildTimeWindows, formatWindows } from "@/features/planning/utils/month.summary";
import { MonthMiniGantt } from "@/features/planning/components/MonthMiniGantt";

function dayNumber(iso: string) {
  return iso.slice(8, 10);
}

function DayTypeBadge({ dayType }: { dayType: string }) {
  const label =
    dayType === "working" ? "Travail" :
    dayType === "rest" ? "Repos" :
    dayType === "absence" ? "Absence" :
    dayType === "unknown" ? "—" :
    dayType;

  const cls =
    dayType === "working"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : dayType === "rest"
      ? "bg-slate-50 text-slate-700 border-slate-200"
      : dayType === "absence"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : "bg-muted text-muted-foreground border-border";

  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${cls}`}>
      {label}
    </span>
  );
}

export function MonthDayCell(props: {
  day: AgentDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  onSelect: () => void;
  posteNameById: Map<number, string>; // gardé même si on ne l’utilise plus ici (tu peux le retirer si tu veux)
}) {
  const { day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect } = props;

  // ✅ résumé intelligent par "fenêtres" (évite le 00:00–24:00 mensonger)
  const windows = buildTimeWindows(day.segments, 60);
  const timeText = formatWindows(windows, 2);

  return (
    <button
      onClick={onSelect}
      aria-pressed={isSelected}
      className={[
        "w-full text-left rounded-2xl border p-2 transition",
        "border-border bg-card hover:bg-muted/50",
        isOutsideMonth ? "opacity-50" : "",
        isInSelectedWeek ? "ring-1 ring-border" : "",
        isSelected ? "ring-2 ring-foreground/60" : "",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm font-semibold text-foreground tabular-nums">
          {dayNumber(day.day_date)}
        </div>
        <DayTypeBadge dayType={day.day_type} />
      </div>

      <div className="mt-1 truncate text-[12px] text-muted-foreground">
        {timeText}
      </div>

      {/* ✅ mini timeline multi segments + chevauchements */}
      {day.segments.length > 0 ? (
        <MonthMiniGantt segments={day.segments} dayStart="00:00:00" dayEnd="24:00:00" maxLanes={2} />
      ) : null}
    </button>
  );
}
