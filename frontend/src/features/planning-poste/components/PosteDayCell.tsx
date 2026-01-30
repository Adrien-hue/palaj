import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { PosteMiniGantt } from "./PosteMiniGantt";
import { Badge } from "@/components/ui/badge";
import { PlanningDayCellFrame } from "@/components/planning/PlanningDayCellFrame";
import { cn } from "@/lib/utils";

import {
  Tooltip,
  TooltipContent,
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
  isOutsideRange,
  onSelect,
}: {
  day: PosteDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  isOutsideRange?: boolean;
  onSelect: () => void;
}) {
  const { total, covered } = day.coverage;

  const ratio = total > 0 ? `${covered}/${total}` : "—";
  const hasCoverage = day.segments.length > 0;

  const ariaLabel =
    total === 0
      ? `Jour ${dayNumber(day.day_date)}, aucune tranche`
      : `Jour ${dayNumber(day.day_date)}, couverture ${covered} sur ${total}`;

  const label = coverageLabel(total, covered);

  const isCoveragePartial = total > 0 && covered < total;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div>
          <PlanningDayCellFrame
            onSelect={onSelect}
            ariaLabel={ariaLabel}
            pressed={isSelected}
            isOutsideMonth={isOutsideMonth}
            isOutsideRange={isOutsideRange}
            isInSelectedWeek={isInSelectedWeek}
            className={cn(
              isCoveragePartial &&
                !isSelected &&
                "border-amber-500/40 bg-amber-500/5 hover:bg-amber-500/10",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div
                className={cn(
                  "text-sm font-semibold tabular-nums",
                  (isOutsideMonth || isOutsideRange) && "text-muted-foreground",
                )}
              >
                {dayNumber(day.day_date)}
              </div>

              <Badge
                variant={coverageVariant(total, covered)}
                className="shrink-0 tabular-nums"
              >
                {ratio}
              </Badge>
            </div>

            {hasCoverage ? (
              <PosteMiniGantt segments={day.segments} />
            ) : (
              <div className="mt-2 text-[12px] text-muted-foreground">
                Non couvert
              </div>
            )}
          </PlanningDayCellFrame>
        </div>
      </TooltipTrigger>

      <TooltipContent className="max-w-[260px]">
        <div className="space-y-2">
          <div className="text-xs font-medium">Couverture</div>

          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-muted-foreground">{label}</span>
            <span className="tabular-nums text-muted-foreground/80">
              {ratio}
            </span>
          </div>

          {total > 0 ? (
            <div className="text-xs text-muted-foreground">
              {covered} / {total} tranches couvertes
            </div>
          ) : null}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
