import type { PostePlanning } from "@/types/postePlanning";
import type { Tranche, Agent } from "@/types";
import type {
  PostePlanningVm,
  PosteDayVm,
  PosteShiftSegmentVm,
} from "./postePlanning.vm";

import { addDaysISO, parseTimeToMinutes } from "@/features/planning/utils/planning.utils";

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

function splitOvernightPerAgent(
  dayDate: string,
  tranche: Tranche,
  agent: Agent,
  allAgents: Agent[]
): Array<{ day_date: string; seg: PosteShiftSegmentVm }> {
  const startMin = parseTimeToMinutes(tranche.heure_debut);
  const endMin = parseTimeToMinutes(tranche.heure_fin);

  // Normal (same day)
  if (endMin >= startMin) {
    return [
      {
        day_date: dayDate,
        seg: makeBaseSeg({
          key: `${dayDate}-${tranche.id}-${agent.id}-${tranche.heure_debut}`,
          day_date: dayDate,
          tranche,
          agent,
          start: tranche.heure_debut,
          end: tranche.heure_fin,
          continuesPrev: false,
          continuesNext: false,
          allAgents,
        }),
      },
    ];
  }

  // Overnight -> split across dayDate and next day
  const nextDay = addDaysISO(dayDate, 1);

  return [
    {
      day_date: dayDate,
      seg: makeBaseSeg({
        key: `${dayDate}-${tranche.id}-${agent.id}-p1`,
        day_date: dayDate,
        tranche,
        agent,
        start: tranche.heure_debut,
        end: "23:59:59",
        continuesPrev: false,
        continuesNext: true,
        allAgents,
      }),
    },
    {
      day_date: nextDay,
      seg: makeBaseSeg({
        key: `${nextDay}-${tranche.id}-${agent.id}-p2`,
        day_date: nextDay,
        tranche,
        agent,
        start: "00:00:00",
        end: tranche.heure_fin,
        continuesPrev: true,
        continuesNext: false,
        allAgents,
      }),
    },
  ];
}

export function buildPostePlanningVm(dto: PostePlanning): PostePlanningVm {
  const dayByDate = new Map(dto.days.map((d) => [d.day_date, d]));

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

  const segByDate = new Map(daysVm.map((d) => [d.day_date, d.segments]));

  // 2) expand covered tranches => 1 segment par agent (+ overnight split)
  for (const dayDto of dto.days) {
    for (const x of dayDto.tranches) {
      const tranche = x.tranche;
      const agents = x.agents ?? [];

      // ✅ On n'ajoute rien si non couvert
      if (agents.length === 0) continue;

      // ✅ 1 barre par agent
      for (const agent of agents) {
        const parts = splitOvernightPerAgent(dayDto.day_date, tranche, agent, agents);

        for (const part of parts) {
          if (!segByDate.has(part.day_date)) continue; // hors range
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
