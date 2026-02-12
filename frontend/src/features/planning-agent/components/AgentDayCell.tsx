import type { AgentDayVm } from "../vm/agentPlanning.vm";
import {
  buildTimeWindows,
  formatWindows,
} from "@/features/planning-agent/utils/month.summary";
import { AgentMiniGantt } from "./AgentMiniGantt";
import { Badge } from "@/components/ui/badge";
import { PlanningDayCellFrame } from "@/components/planning/PlanningDayCellFrame";
import { DayTypeBadge, dayTypeLabel } from "@/components/planning/DayTypeBadge";
import { AgentDayCellTooltip } from "./AgentDayCellTooltip";
import { cn } from "@/lib/utils";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { RhViolation } from "@/types/rhValidation";

function dayNumber(iso: string) {
  return String(Number(iso.slice(8, 10)));
}

type Window = { start: string; end: string };

function pickPrimaryWindow(
  windows: Window[],
  segments: AgentDayVm["segments"],
): Window | null {
  if (windows.length === 0) return null;

  const startingSegs = segments.filter((s) => !s.continuesPrev);
  const primaryStart = startingSegs.length
    ? startingSegs.map((s) => s.start).sort((a, b) => a.localeCompare(b))[0]
    : null;

  if (!primaryStart) return windows[0];

  const w = windows.find(
    (x) => x.start <= primaryStart && primaryStart < x.end,
  );
  return w ?? windows[0];
}

function windowLabel(w: Window, index: number, windows: Window[]) {
  if (index === 0 && w.start === "00:00:00") return "← suite";
  if (index === windows.length - 1 && w.end === "23:59:00") return "→ nuit";
  return null;
}

export function AgentDayCell(props: {
  day: AgentDayVm;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  isOutsideRange?: boolean;
  isMultiSelected?: boolean;
  rhViolations?: RhViolation[];
  onSelect: (e: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  const {
    day,
    isOutsideMonth,
    isSelected,
    isInSelectedWeek,
    isOutsideRange,
    isMultiSelected = false,
    rhViolations,
    onSelect,
  } = props;

  const hasSegments = day.segments.length > 0;

  // ZCOT = working without segments (agent à disposition)
  const effectiveDayType =
    day.day_type === "working" && !hasSegments ? "zcot" : day.day_type;

  const isWorkingDay = effectiveDayType === "working";

  // Build windows only for working days with segments
  const windows =
    isWorkingDay && hasSegments
      ? (buildTimeWindows(day.segments, 60) as Window[])
      : [];
  const timeText = windows.length ? formatWindows(windows, 4) : "";

  const hasCarryFromPrev =
    hasSegments && day.segments.some((s) => s.continuesPrev);
  const hasCarryToNext =
    hasSegments && day.segments.some((s) => s.continuesNext);
  const hasOwnStart = hasSegments && day.segments.some((s) => !s.continuesPrev);
  const isCarryOnlyDay = hasSegments && hasCarryFromPrev && !hasOwnStart;

  const primaryWindow = pickPrimaryWindow(windows, day.segments);
  const extraWindowsCount =
    primaryWindow && windows.length > 1 ? windows.length - 1 : 0;

  const ariaParts = [
    `Jour ${dayNumber(day.day_date)}`,
    `Type: ${dayTypeLabel(effectiveDayType)}`,
  ];
  if (isWorkingDay && hasSegments && timeText)
    ariaParts.push(`Horaires: ${timeText}`);
  const ariaLabel = ariaParts.join(", ");

  // --- RH state for this day (tint background) ---
  const rhHasError = (rhViolations?.some((v) => v.severity === "error")) ?? false;
  const rhHasWarn = !rhHasError && ((rhViolations?.some((v) => v.severity === "warning")) ?? false);
  const rhHasInfo =
    !rhHasError && !rhHasWarn && ((rhViolations?.some((v) => v.severity === "info")) ?? false);

  const tone =
    rhHasError ? "danger" : rhHasWarn ? "warning" : rhHasInfo ? "info" : "none";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div>
          <PlanningDayCellFrame
            onSelect={onSelect}
            ariaLabel={ariaLabel}
            pressed={isSelected}
            multiSelected={isMultiSelected}
            isOutsideMonth={isOutsideMonth}
            isOutsideRange={isOutsideRange}
            isInSelectedWeek={isInSelectedWeek}
            tone={tone}
          >
            <div className="relative">
              <div className="relative">
                <div className="flex items-start justify-between gap-2">
                  <div
                    className={cn(
                      "text-sm font-semibold tabular-nums",
                      (isOutsideMonth || isOutsideRange) &&
                        "text-muted-foreground",
                    )}
                  >
                    {dayNumber(day.day_date)}
                  </div>
                  <DayTypeBadge dayType={effectiveDayType} />
                </div>

                {/* Secondary line: depends on day type */}
                <div className="mt-1 flex items-center gap-2">
                  {isWorkingDay && hasSegments ? (
                    <>
                      <Badge variant="secondary" className="tabular-nums">
                        {primaryWindow
                          ? `${primaryWindow.start.slice(0, 5)}–${primaryWindow.end.slice(0, 5)}`
                          : "—"}
                        {hasCarryToNext ? " →" : ""}
                      </Badge>

                      {isCarryOnlyDay ? (
                        <Badge
                          variant="outline"
                          className="text-muted-foreground"
                        >
                          ← Suite
                        </Badge>
                      ) : null}

                      {extraWindowsCount > 0 ? (
                        <Badge
                          variant="outline"
                          className="tabular-nums text-muted-foreground"
                        >
                          +{extraWindowsCount}
                        </Badge>
                      ) : null}
                    </>
                  ) : (
                    <div className="text-[12px] text-muted-foreground">
                      {dayTypeLabel(effectiveDayType)}
                    </div>
                  )}
                </div>

                {/* Timeline only for working days with segments */}
                {isWorkingDay && hasSegments ? (
                  <div className="mt-2">
                    <AgentMiniGantt
                      segments={day.segments}
                      dayStart="00:00:00"
                      dayEnd="24:00:00"
                      maxLanes={2}
                    />
                  </div>
                ) : null}
              </div>
            </div>
          </PlanningDayCellFrame>
        </div>
      </TooltipTrigger>

      <TooltipContent className="max-w-[320px]">
        <AgentDayCellTooltip
          day={day}
          windows={windows}
          effectiveDayType={effectiveDayType}
          rhViolations={rhViolations ?? []}
        />
      </TooltipContent>
    </Tooltip>
  );
}
