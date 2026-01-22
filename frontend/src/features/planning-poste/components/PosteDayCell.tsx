import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { PosteMiniGantt } from "./PosteMiniGantt";
import { Badge } from "@/components/ui/badge";

function dayNumber(iso: string) {
  return iso.slice(8, 10);
}

function coverageVariant(total: number, covered: number) {
  if (total === 0) return "secondary";
  if (covered >= total) return "success";
  return "warning";
}

export function PosteDayCell({
  day,
  isOutsideMonth,
  isSelected,
  isInSelectedWeek,
  onSelect,
}: {
  day: PosteDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  onSelect: () => void;
}) {
  const { total, covered } = day.coverage;

  const ratio = total > 0 ? `${covered}/${total}` : "—";
  const hasCoverage = day.segments.length > 0;

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
      className={[
        "w-full text-left rounded-xl border p-2 transition",
        "border-[color:var(--app-border)] bg-[color:var(--app-surface)] hover:bg-[color:var(--app-soft)]",
        isOutsideMonth ? "opacity-50" : "",
        isInSelectedWeek ? "ring-1 ring-[color:var(--app-border)]" : "",
        isSelected ? "ring-2 ring-[color:var(--app-ring)]" : "",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm font-semibold tabular-nums text-[color:var(--app-text)]">
          {dayNumber(day.day_date)}
        </div>

        <Badge
          variant={coverageVariant(total, covered)}
          className="shrink-0 tabular-nums"
          title={
            total === 0
              ? "Aucune tranche"
              : covered >= total
              ? "Couverture complète"
              : "Couverture incomplète"
          }
        >
          {ratio}
        </Badge>
      </div>

      {hasCoverage ? (
        <PosteMiniGantt segments={day.segments} />
      ) : (
        <div className="mt-2 text-[12px] text-[color:var(--app-muted)]">
          Non couvert
        </div>
      )}
    </button>
  );
}
