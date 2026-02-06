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

type CoverageVariant = "secondary" | "success" | "warning";

function coverageVariant(day: PosteDayVm): CoverageVariant {
  const { required, missing, isConfigured } = day.coverage;

  if (!isConfigured) return "secondary";
  if (required === 0) return "secondary";
  return missing === 0 ? "success" : "warning";
}

function coverageLabel(day: PosteDayVm) {
  const { required, missing, isConfigured } = day.coverage;

  if (!isConfigured) return "Couverture non configurée";
  if (required === 0) return "Aucun besoin configuré";
  if (missing === 0) return "Couverture complète";
  return "Couverture incomplète";
}

function coverageRatio(day: PosteDayVm) {
  const { required, assigned, isConfigured } = day.coverage;
  if (!isConfigured) return "—";
  return required > 0 ? `${assigned}/${required}` : "0/0";
}

export function PosteDayCell({
  day,
  isOutsideMonth,
  isSelected,
  isInSelectedWeek,
  isOutsideRange,
  multiSelect = false,
  isMultiSelected = false,
  onSelect,
}: {
  day: PosteDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  isOutsideRange?: boolean;

  /** multi-select */
  multiSelect?: boolean;
  isMultiSelected?: boolean;

  onSelect: (e: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  const { required, assigned, missing, isConfigured } = day.coverage;

  const ratio = coverageRatio(day);
  const label = coverageLabel(day);

  const hasCoverage = day.segments.length > 0;

  const ariaLabel = !isConfigured
    ? `Jour ${dayNumber(day.day_date)}, couverture non configurée`
    : required === 0
      ? `Jour ${dayNumber(day.day_date)}, aucun besoin configuré`
      : missing === 0
        ? `Jour ${dayNumber(day.day_date)}, couverture complète (${assigned} sur ${required})`
        : `Jour ${dayNumber(day.day_date)}, sous-couverture (${assigned} sur ${required}, manque ${missing})`;

  const isCoveragePartial = isConfigured && required > 0 && missing > 0;

  // Visuel multi-selection
  const multiSelectedRing =
    isMultiSelected && !isSelected
      ? "ring-2 ring-primary ring-offset-2 ring-offset-background"
      : null;

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
              // multi-select highlight
              multiSelectedRing,

              // sous-couverture : conserver ton style, mais ne pas écraser une sélection
              isCoveragePartial &&
                !isSelected &&
                !isMultiSelected &&
                "border-amber-500/40 bg-amber-500/5 hover:bg-amber-500/10",

              // en mode multi, on rend le hover plus explicite
              multiSelect && !isSelected && "hover:bg-muted/40",
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
                variant={coverageVariant(day)}
                className="shrink-0 tabular-nums"
                title={label}
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

      <TooltipContent className="max-w-[280px]">
        <div className="space-y-2">
          <div className="text-xs font-medium">Couverture</div>

          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-muted-foreground">{label}</span>
            <span className="tabular-nums text-muted-foreground/80">{ratio}</span>
          </div>

          {!isConfigured ? (
            <div className="text-xs text-muted-foreground">
              Aucune règle de couverture n’est configurée pour ce jour.
            </div>
          ) : required === 0 ? (
            <div className="text-xs text-muted-foreground">
              Besoin total : <span className="tabular-nums">0</span>
            </div>
          ) : (
            <div className="space-y-1 text-xs text-muted-foreground">
              <div className="flex items-center justify-between gap-2">
                <span>Besoin</span>
                <span className="tabular-nums">{required}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span>Affectés</span>
                <span className="tabular-nums">{assigned}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span>Manque</span>
                <span className="tabular-nums">{missing}</span>
              </div>
            </div>
          )}

          {!hasCoverage ? (
            <div className="pt-1 text-[12px] text-muted-foreground/80">
              Aucun segment planifié sur la journée.
            </div>
          ) : null}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
