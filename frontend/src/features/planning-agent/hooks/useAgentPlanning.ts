"use client";

import useSWR from "swr";
import { AgentPlanningKey } from "./agentPlanning.key";
import { getAgentPlanning } from "@/services/planning.service";
import type { AgentPlanning } from "@/types";

type Params = {
  agentId: number | null;
  startDate: string;
  endDate: string;
};

function keyOf(p: Params): AgentPlanningKey | null {
  if (!p.agentId) return null;
  return ["agentPlanning", p.agentId, p.startDate, p.endDate];
}

export function useAgentPlanning(p: Params) {
  return useSWR<AgentPlanning, Error, AgentPlanningKey | null>(
    keyOf(p),
    ([, agentId, startDate, endDate]) =>
      getAgentPlanning(agentId, { startDate, endDate }).then((res) => {
        if (!Array.isArray((res as any)?.days)) {
          console.warn("AgentPlanning.days is not array", res);
        }
        
        return res;
      }),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    },
  );
}
