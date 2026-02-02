import type { PostePlanning } from "@/types/postePlanning";
import type { Tranche, Agent } from "@/types";
import type {
  PostePlanningVm,
  PosteDayVm,
  PosteShiftSegmentVm,
} from "./postePlanning.vm";
import type { PosteCoverageConfigVm } from "./posteCoverageConfig.vm.builder";

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
    coverage: { required: 0, assigned: 0, missing: 0, isConfigured: false },
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
  const {
    key,
    tranche,
    agent,
    start,
    end,
    continuesPrev,
    continuesNext,
    allAgents,
  } = args;

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
  const { day_date, trancheId, agentId, start, continuesPrev, continuesNext } =
    args;

  if (continuesNext) return `${day_date}-${trancheId}-${agentId}-p1`;
  if (continuesPrev) return `${day_date}-${trancheId}-${agentId}-p2`;
  return `${day_date}-${trancheId}-${agentId}-${start}`;
}

function weekdayMon0FromIsoDate(isoDate: string): number {
  const js = new Date(isoDate + "T00:00:00").getDay(); // 0=dimanche
  return (js + 6) % 7; // 0=lundi ... 6=dimanche
}

type Input = { tranche: Tranche; agent: Agent; allAgents: Agent[] };

export function buildPostePlanningVm(
  dto: PostePlanning,
  opts?: { coverageConfig?: PosteCoverageConfigVm | null },
): PostePlanningVm {
  const dayByDate = new Map(dto.days.map((d) => [d.day_date, d] as const));

  // 1) init full range
  const daysVm: PosteDayVm[] = [];
  let cur = dto.start_date;

  while (cur <= dto.end_date) {
    const dayDto = dayByDate.get(cur);

    if (!dayDto) {
      daysVm.push(emptyDay(cur));
    } else {
      const cfg = opts?.coverageConfig;
      const weekday = weekdayMon0FromIsoDate(dayDto.day_date);

      const getRequired = (trancheId: number) =>
        cfg?.requiredByWeekday[weekday]?.[trancheId];

      const tranches = dayDto.tranches.map((x) => {
        const agents = x.agents ?? [];
        const trancheId = x.tranche.id;

        const required = getRequired(trancheId);
        const assigned = agents.length;

        return {
          tranche: x.tranche,
          agents,
          coverage: {
            required: required ?? 0,
            assigned,
            delta: assigned - (required ?? 0),
            isConfigured: required != null,
          },
        };
      });

      const requiredTotal = tranches.reduce(
        (acc, t) => acc + (t.coverage?.required ?? 0),
        0,
      );
      const assignedTotal = tranches.reduce(
        (acc, t) => acc + (t.coverage?.assigned ?? 0),
        0,
      );

      const missingTotal = tranches.reduce((acc, t) => {
        const required = t.coverage?.required ?? 0;
        const assigned = t.coverage?.assigned ?? 0;
        return acc + Math.max(0, required - assigned);
      }, 0);

      const isConfigured =
        cfg?.requiredByWeekday[weekday] != null &&
        Object.keys(cfg.requiredByWeekday[weekday]).length > 0;

      daysVm.push({
        day_date: dayDto.day_date,
        day_type: dayDto.day_type,
        description: dayDto.description ?? null,
        is_off_shift: !!dayDto.is_off_shift,
        tranches,
        segments: [],
        coverage: {
          required: requiredTotal,
          assigned: assignedTotal,
          missing: missingTotal,
          isConfigured,
        },
      });
    }

    cur = addDaysISO(cur, 1);
  }

  const segByDate = new Map(
    daysVm.map((d) => [d.day_date, d.segments] as const),
  );

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
            }),
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
