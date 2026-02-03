"use client";

import useSWR from "swr";
import { getTeamPlanning } from "@/services/planning.service";
import type { TeamPlanning } from "@/types/teamPlanning";

type Params = {
  teamId: number | null;
  startDate: string;
  endDate: string;
};

type TeamPlanningKey = readonly ["teamPlanning", number, string, string];

function keyOf(p: Params): TeamPlanningKey | null {
  if (!p.teamId) return null;
  return ["teamPlanning", p.teamId, p.startDate, p.endDate];
}

export function useTeamPlanning(p: Params) {
  return useSWR<TeamPlanning, Error, TeamPlanningKey | null>(
    keyOf(p),
    ([, teamId, startDate, endDate]) =>
      getTeamPlanning(teamId, { startDate, endDate }),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  );
}
