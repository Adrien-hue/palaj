"use client";

import type { AgentDayVm } from "../vm/agentPlanning.vm";
import type { RhViolation } from "@/types/rhValidation";
import { RhDayTooltip } from "@/features/rh-validation/components/RhDayTooltip";

export function AgentDayCellTooltip({
  day,
  windows,
  effectiveDayType,
  rhViolations,
}: {
  day: AgentDayVm;
  windows: { start: string; end: string }[];
  effectiveDayType: AgentDayVm["day_type"] | "zcot";
  rhViolations: RhViolation[];
}) {
  const dateISO = day.day_date.slice(0, 10);

  return (
    <RhDayTooltip
      dateISO={dateISO}
      dayType={effectiveDayType}
      description={day.description}
      windows={windows}
      rhViolations={rhViolations}
      showRhInfos={true}
    />
  );
}
