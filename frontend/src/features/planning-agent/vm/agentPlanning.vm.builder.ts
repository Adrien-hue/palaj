import type { AgentPlanning, Tranche } from "@/types";
import type {
  AgentPlanningVm,
  AgentDayVm,
  ShiftSegmentVm,
} from "./agentPlanning.vm";

import { addDaysISO } from "@/utils/date.format";
import { splitOvernight } from "@/features/planning-common/timeline/splitOvernight";

function emptyDay(day_date: string): AgentDayVm {
  return {
    day_date,
    day_type: "unknown",
    description: null,
    is_off_shift: false,
    tranche_id: null,
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

function toDayVm(dayDto: AgentPlanning["days"][number]): AgentDayVm {
  return {
    day_date: dayDto.day_date,
    day_type: dayDto.day_type,
    description: dayDto.description,
    is_off_shift: dayDto.is_off_shift,
    // V1: 1 seule tranche max => on prend la première si elle existe
    tranche_id: dayDto.tranches[0]?.id ?? null,
    segments: [],
  };
}

export function buildPlanningVm(dto: AgentPlanning): AgentPlanningVm {
  // 1) safe access to days (SWR cache might transiently contain bad shape)
  const safeDays = Array.isArray(dto.days) ? dto.days : [];
  const dayByDate = new Map(safeDays.map((d) => [d.day_date, d] as const));

  // 2) init full range
  const daysVm: AgentDayVm[] = [];
  let cur = dto.start_date;

  while (cur <= dto.end_date) {
    const dayDto = dayByDate.get(cur);
    daysVm.push(dayDto ? toDayVm(dayDto) : emptyDay(cur));
    cur = addDaysISO(cur, 1);
  }

  const segByDate = new Map(
    daysVm.map((d) => [d.day_date, d.segments] as const),
  );

  // 3) split + distribute segments
  for (const dayDto of safeDays) {
    for (const t of dayDto.tranches) {
      const parts = splitOvernight<Tranche, ShiftSegmentVm>(
        {
          dayDate: dayDto.day_date,
          input: t,
          start: t.heure_debut,
          end: t.heure_fin,
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
        }),
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
