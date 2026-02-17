import type { AgentDay, RhViolation } from "@/types";
import { RhDayTooltip } from "@/features/rh-validation/components/RhDayTooltip";

export function TeamDayCellTooltip({
  day,
  rhViolations,
}: {
  day: AgentDay;
  rhViolations: RhViolation[];
}) {
  const dateISO = day.day_date.slice(0, 10);
  return (
    <RhDayTooltip
      dateISO={dateISO}
      dayType={day.day_type}
      description={day.description}
      tranches={day.tranches ?? []}
      isOffShift={!!day.is_off_shift}
      rhViolations={rhViolations}
      showRhInfos={false} // 👈 recommandé en team
    />
  );
}
