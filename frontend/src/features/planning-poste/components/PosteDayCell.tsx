import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { PosteMiniGantt } from "./PosteMiniGantt";
import { Badge } from "@/components/ui/badge";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function dayNumber(iso: string) {
  return String(Number(iso.slice(8, 10)));
}

function coverageVariant(total: number, covered: number) {
  if (total === 0) return "secondary";
  if (covered >= total) return "success";
  return "warning";
}

function coverageLabel(total: number, covered: number) {
  if (total === 0) return "Aucune tranche";
  if (covered >= total) return "Couverture complète";
  return "Couverture incomplète";
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

  const ariaLabel =
    total === 0
      ? `Jour ${dayNumber(day.day_date)}, aucune tranche`
      : `Jour ${dayNumber(day.day_date)}, couverture ${covered} sur ${total}`;

  const ringClass = isSelected
    ? "ring-2 ring-[color:var(--app-ring)]"
    : isInSelectedWeek
    ? "ring-1 ring-[color:var(--app-border)]"
    : "";

  const tooltipText = `${coverageLabel(total, covered)} • ${ratio}`;

  return (
    <TooltipProvider>
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
          <div className="text-sm font-semibold tabular-nums text-[color:var(--app-text)]">
            {dayNumber(day.day_date)}
          </div>

          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant={coverageVariant(total, covered)}
                className="shrink-0 tabular-nums"
                tabIndex={0}
              >
                {ratio}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>{tooltipText}</TooltipContent>
          </Tooltip>
        </div>

        {hasCoverage ? (
          <PosteMiniGantt segments={day.segments} />
        ) : (
          <div className="mt-2 text-[12px] text-[color:var(--app-muted)]">
            Non couvert
          </div>
        )}
      </button>
    </TooltipProvider>
  );
}
