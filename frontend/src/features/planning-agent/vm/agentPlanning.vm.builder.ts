import type { AgentPlanning, Tranche } from "@/types";
import type { AgentPlanningVm, AgentDayVm, ShiftSegmentVm } from "./agentPlanning.vm";

import { addDaysISO } from "@/utils/date.format";
import { splitOvernight } from "@/features/planning-common/timeline/splitOvernight";

function emptyDay(day_date: string): AgentDayVm {
  return {
    day_date,
    day_type: "unknown",
    description: null,
    is_off_shift: false,
    segments: [],
  };
}

function segKey(args: {
  day_date: string;
  trancheId: number;
  start: string;
  continuesPrev: boolean;
  continuesNext: boolean;
}) {
  const { day_date, trancheId, start, continuesPrev, continuesNext } = args;

  if (continuesNext) return `${day_date}-${trancheId}-p1`;
  if (continuesPrev) return `${day_date}-${trancheId}-p2`;
  return `${day_date}-${trancheId}-${start}`;
}

export function buildPlanningVm(dto: AgentPlanning): AgentPlanningVm {
  // 1) map date -> day dto (for type/desc/off_shift)
  const dayByDate = new Map(dto.days.map((d) => [d.day_date, d] as const));

  // 2) init full range
  const daysVm: AgentDayVm[] = [];
  let cur = dto.start_date;

  while (cur <= dto.end_date) {
    const dayDto = dayByDate.get(cur);
    daysVm.push(dayDto ? { ...dayDto, segments: [] } : emptyDay(cur));
    cur = addDaysISO(cur, 1);
  }

  const segByDate = new Map(daysVm.map((d) => [d.day_date, d.segments] as const));

  // 3) split + distribute segments
  for (const dayDto of dto.days) {
    for (const t of dayDto.tranches) {
      const parts = splitOvernight<Tranche, ShiftSegmentVm>(
        {
          dayDate: dayDto.day_date,
          input: t,
          start: t.heure_debut,
          end: t.heure_fin,
          // align with your previous agent builder
          endOfDay: "23:59:00",
          startOfDay: "00:00:00",
        },
        ({ day_date, start, end, continuesPrev, continuesNext, input }) => ({
          key: segKey({
            day_date,
            trancheId: input.id,
            start,
            continuesPrev,
            continuesNext,
          }),
          sourceTrancheId: input.id,
          nom: input.nom,
          posteId: input.poste_id,
          start,
          end,
          continuesPrev,
          continuesNext,
          color: input.color,
        })
      );

      for (const part of parts) {
        if (!segByDate.has(part.day_date)) continue; // out of range (rare)
        segByDate.get(part.day_date)!.push(part.seg);
      }
    }
  }

  // 4) sort segments inside each day
  for (const d of daysVm) {
    d.segments.sort((a, b) => a.start.localeCompare(b.start));
  }

  return {
    agent: dto.agent,
    start_date: dto.start_date,
    end_date: dto.end_date,
    days: daysVm,
  };
}
