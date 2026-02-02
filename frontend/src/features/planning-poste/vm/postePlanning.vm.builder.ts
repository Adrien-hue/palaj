import type { PostePlanning } from "@/types/postePlanning";
import type { Tranche, Agent } from "@/types";
import type { PostePlanningVm, PosteDayVm, PosteShiftSegmentVm } from "./postePlanning.vm";

import { addDaysISO } from "@/utils/date.format";
import { splitOvernight } from "@/features/planning-common/timeline/splitOvernight";

function emptyDay(day_date: string): PosteDayVm {
  return {
    day_date,
    day_type: "unknown",
    description: null,
    is_off_shift: false,
    tranches: [],
    segments: [],
    coverage: { total: 0, covered: 0 },
  };
}

function makeBaseSeg(args: {
  key: string;
  day_date: string;
  tranche: Tranche;
  agent: Agent;
  start: string;
  end: string;
  continuesPrev: boolean;
  continuesNext: boolean;
  allAgents?: Agent[];
}): PosteShiftSegmentVm {
  const { key, tranche, agent, start, end, continuesPrev, continuesNext, allAgents } = args;

  return {
    key,
    sourceTrancheId: tranche.id,
    nom: tranche.nom,
    posteId: tranche.poste_id,
    start,
    end,
    continuesPrev,
    continuesNext,
    agent,
    agents: allAgents,
  };
}

function segKey(args: {
  day_date: string;
  trancheId: number;
  agentId: number;
  start: string;
  continuesPrev: boolean;
  continuesNext: boolean;
}) {
  const { day_date, trancheId, agentId, start, continuesPrev, continuesNext } = args;

  if (continuesNext) return `${day_date}-${trancheId}-${agentId}-p1`;
  if (continuesPrev) return `${day_date}-${trancheId}-${agentId}-p2`;
  return `${day_date}-${trancheId}-${agentId}-${start}`;
}

type Input = { tranche: Tranche; agent: Agent; allAgents: Agent[] };

export function buildPostePlanningVm(dto: PostePlanning): PostePlanningVm {
  const dayByDate = new Map(dto.days.map((d) => [d.day_date, d] as const));

  // 1) init full range
  const daysVm: PosteDayVm[] = [];
  let cur = dto.start_date;

  while (cur <= dto.end_date) {
    const dayDto = dayByDate.get(cur);

    if (!dayDto) {
      daysVm.push(emptyDay(cur));
    } else {
      const total = dayDto.tranches.length;
      const covered = dayDto.tranches.filter((x) => (x.agents?.length ?? 0) > 0).length;

      daysVm.push({
        day_date: dayDto.day_date,
        day_type: dayDto.day_type,
        description: dayDto.description ?? null,
        is_off_shift: !!dayDto.is_off_shift,
        tranches: dayDto.tranches.map((x) => ({
          tranche: x.tranche,
          agents: x.agents ?? [],
        })),
        segments: [],
        coverage: { total, covered },
      });
    }

    cur = addDaysISO(cur, 1);
  }

  const segByDate = new Map(daysVm.map((d) => [d.day_date, d.segments] as const));

  // 2) expand covered tranches => 1 segment per agent (+ overnight split)
  for (const dayDto of dto.days) {
    for (const x of dayDto.tranches) {
      const tranche = x.tranche;
      const agents = x.agents ?? [];

      // ✅ no segment when not covered
      if (agents.length === 0) continue;

      for (const agent of agents) {
        const parts = splitOvernight<Input, PosteShiftSegmentVm>(
          {
            dayDate: dayDto.day_date,
            input: { tranche, agent, allAgents: agents },
            start: tranche.heure_debut,
            end: tranche.heure_fin,
            // align with your previous poste builder
            endOfDay: "23:59:59",
            startOfDay: "00:00:00",
          },
          ({ day_date, start, end, continuesPrev, continuesNext, input }) =>
            makeBaseSeg({
              key: segKey({
                day_date,
                trancheId: input.tranche.id,
                agentId: input.agent.id,
                start,
                continuesPrev,
                continuesNext,
              }),
              day_date,
              tranche: input.tranche,
              agent: input.agent,
              start,
              end,
              continuesPrev,
              continuesNext,
              allAgents: input.allAgents,
            })
        );

        for (const part of parts) {
          if (!segByDate.has(part.day_date)) continue; // out of range
          segByDate.get(part.day_date)!.push(part.seg);
        }
      }
    }
  }

  // 3) sort segments inside each day
  for (const d of daysVm) {
    d.segments.sort((a, b) => a.start.localeCompare(b.start));
  }

  return {
    poste: dto.poste,
    start_date: dto.start_date,
    end_date: dto.end_date,
    days: daysVm,
  };
}
