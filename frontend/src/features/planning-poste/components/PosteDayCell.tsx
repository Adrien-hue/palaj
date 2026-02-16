import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { PosteMiniGantt } from "./PosteMiniGantt";
import { PosteCoverageBadge } from "./PosteCoverageBadge";
import {
  computeTrancheCoverageCounts,
  trancheCoverageLabel,
  trancheCoverageRatio,
} from "@/features/planning-poste/utils/posteCoverageTranches";

import { Badge } from "@/components/ui/badge";
import { PlanningDayCellFrame } from "@/components/planning/PlanningDayCellFrame";
import { cn } from "@/lib/utils";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import type { RhDaySummary } from "@/types";
import { computePosteDayTone } from "@/features/planning-poste/utils/posteDayTone";

function dayNumber(iso: string) {
  return String(Number(iso.slice(8, 10)));
}

function rhRiskLabel(risk: RhDaySummary["risk"]) {
  if (risk === "high") return "Élevé";
  if (risk === "medium") return "Moyen";
  if (risk === "low") return "Faible";
  return "Aucun";
}

export function PosteDayCell({
  day,
  rhSummary,
  isOutsideMonth,
  isSelected,
  isInSelectedWeek,
  isOutsideRange,
  multiSelect = false,
  isMultiSelected = false,
  onSelect,
}: {
  day: PosteDayVm;
  rhSummary?: RhDaySummary | undefined;

  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  isOutsideRange?: boolean;

  /** multi-select */
  multiSelect?: boolean;
  isMultiSelected?: boolean;

  onSelect: (e: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  const trancheCov = computeTrancheCoverageCounts(day);
  const label = trancheCoverageLabel(trancheCov);
  const ratio = trancheCoverageRatio(trancheCov);
  const showNoTrancheCovered = trancheCov.isConfigured && trancheCov.total > 0 && trancheCov.covered === 0;

  const hasCoverage = day.segments.length > 0;

  const ariaLabel = !trancheCov.isConfigured
  ? `Jour ${dayNumber(day.day_date)}, couverture non configurée`
  : trancheCov.total === 0
    ? `Jour ${dayNumber(day.day_date)}, aucune tranche attendue`
    : trancheCov.missing === 0
      ? `Jour ${dayNumber(day.day_date)}, couverture complète (${trancheCov.covered} sur ${trancheCov.total} tranches)`
      : `Jour ${dayNumber(day.day_date)}, sous-couverture (${trancheCov.covered} sur ${trancheCov.total} tranches, manque ${trancheCov.missing})`;


  // Visuel multi-selection
  const multiSelectedRing =
    isMultiSelected && !isSelected
      ? "ring-2 ring-primary ring-offset-2 ring-offset-background"
      : null;

  // RH
  const rhBlockers = rhSummary?.agents_with_blockers_count ?? 0;
  const rhIssues = rhSummary?.agents_with_issues_count ?? 0;

  const rhBadge =
    rhBlockers > 0
      ? { count: rhBlockers, variant: "destructive" as const, title: `${rhBlockers} agent(s) bloquant(s) RH` }
      : rhIssues > 0
        ? { count: rhIssues, variant: "secondary" as const, title: `${rhIssues} agent(s) avec alerte RH` }
        : null;

  const tone = computePosteDayTone({
    day,
    rh: rhSummary,
    isOutsideMonth,
    isOutsideRange,
  });

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div>
          <PlanningDayCellFrame
            tone={tone}
            onSelect={onSelect}
            ariaLabel={ariaLabel}
            pressed={isSelected}
            isOutsideMonth={isOutsideMonth}
            isOutsideRange={isOutsideRange}
            isInSelectedWeek={isInSelectedWeek}
            className={cn(
              // multi-select highlight
              multiSelectedRing,
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

              <div className="flex items-center gap-2">
                {rhBadge ? (
                  <Badge
                    variant={rhBadge.variant}
                    className="shrink-0 tabular-nums"
                    title={rhBadge.title}
                  >
                    {rhBadge.count}
                  </Badge>
                ) : null}

                <PosteCoverageBadge day={day} />
              </div>
            </div>

            {hasCoverage ? (
              <PosteMiniGantt segments={day.segments} />
            ) : showNoTrancheCovered ? (
              <div className="mt-2 text-[12px] text-muted-foreground">
                Aucune tranche couverte
              </div>
            ) : (
              <div className="mt-2 text-[12px] text-muted-foreground">
                —
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
            <span className="tabular-nums text-muted-foreground/80">
              {ratio}
            </span>
          </div>

          {!trancheCov.isConfigured ? (
            <div className="text-xs text-muted-foreground">
              Aucune règle de couverture n’est configurée pour ce jour.
            </div>
          ) : trancheCov.total === 0 ? (
            <div className="text-xs text-muted-foreground">
              Aucune tranche attendue pour ce jour.
            </div>
          ) : (
            <div className="space-y-1 text-xs text-muted-foreground">
              <div className="flex items-center justify-between gap-2">
                <span>Tranches attendues</span>
                <span className="tabular-nums">{trancheCov.total}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span>Tranches couvertes</span>
                <span className="tabular-nums">{trancheCov.covered}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span>Tranches non couvertes</span>
                <span className="tabular-nums">{trancheCov.missing}</span>
              </div>
            </div>
          )}

          {rhSummary ? (
            <div className="pt-2 border-t">
              <div className="text-xs font-medium">Validation RH</div>

              <div className="mt-1 flex items-center justify-between gap-2 text-xs">
                <span className="text-muted-foreground">Risque</span>
                <span className="tabular-nums text-muted-foreground/80">
                  {rhRiskLabel(rhSummary.risk)}
                </span>
              </div>

              {rhSummary.agents_with_blockers_count > 0 ||
              rhSummary.agents_with_issues_count > 0 ? (
                <div className="mt-1 space-y-1 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between gap-2">
                    <span>Agents avec blocants</span>
                    <span className="tabular-nums">
                      {rhSummary.agents_with_blockers_count}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <span>Agents avec alertes</span>
                    <span className="tabular-nums">
                      {rhSummary.agents_with_issues_count}
                    </span>
                  </div>

                  {rhSummary.top_triggers?.length ? (
                    <div className="pt-1">
                      <div className="text-[11px] text-muted-foreground/80">
                        Top triggers
                      </div>
                      <ul className="mt-1 space-y-0.5">
                        {rhSummary.top_triggers.slice(0, 3).map((t) => (
                          <li
                            key={t.key}
                            className="flex items-center justify-between gap-2"
                          >
                            <span className="truncate">{t.key}</span>
                            <span className="tabular-nums text-muted-foreground/80">
                              x{t.count}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="mt-1 text-xs text-muted-foreground">
                  Aucun signal RH sur la journée.
                </div>
              )}
            </div>
          ) : null}

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
