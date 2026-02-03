import type { TeamPlanning } from "@/types/teamPlanning";
import type { AgentDay } from "@/types";
import { TeamPlanningVm } from "./teamPlanning.vm";

function emptyDay(day_date: string): AgentDay {
  return {
    day_date,
    day_type: "unknown",
    description: null,
    is_off_shift: false,
    tranches: [],
  };
}

const normalizeDay = (d: AgentDay): AgentDay => ({
  ...d,
  tranches: (d.tranches ?? []).slice().sort((a, b) => a.heure_debut.localeCompare(b.heure_debut)),
});


export function buildTeamPlanningVm(dto: TeamPlanning): TeamPlanningVm {
  const days = dto.days ?? [];

  const rows = (dto.agents ?? []).map((row) => {
    const dayByDate = new Map((row.days ?? []).map((d) => [d.day_date, d] as const));

    return {
      agent: row.agent,
      days: days.map((date) => normalizeDay(dayByDate.get(date) ?? emptyDay(date))),
    };
  });

  return {
    team: dto.team,
    start_date: dto.start_date,
    end_date: dto.end_date,
    days,
    rows,
  };
}
