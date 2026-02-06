"use client";

import useSWR from "swr";
import { postAgentPlanningDayBatch } from "@/services/agent-planning.service";
import type { AgentSelectStatusById } from "@/features/agents/components/agentSelect.types";

function uniqSorted(ids: number[]) {
  return Array.from(new Set(ids)).sort((a, b) => a - b);
}

function pickPrimaryTranche(tranches: Array<{ heure_debut?: string; nom: string; color?: string | null }>) {
  if (!tranches?.length) return null;
  return [...tranches].sort((a, b) =>
    (a.heure_debut ?? "").localeCompare(b.heure_debut ?? "")
  )[0];
}

export function useAgentDayStatusesBatch(params: {
  dayDate: string | null;
  agentIds: number[];
}) {
  const dayDate = params.dayDate;
  const agentIds = uniqSorted(params.agentIds);

  const key =
    dayDate && agentIds.length
      ? (["agent-day-status-batch", dayDate, ...agentIds] as const)
      : null;

  const swr = useSWR<AgentSelectStatusById, Error>(
    key,
    async () => {
      const res = await postAgentPlanningDayBatch({
        day_date: dayDate!,
        agent_ids: agentIds,
      });

      const map: AgentSelectStatusById = new Map();

      for (const it of res.items ?? []) {
        const pd = it.planning_day;
        const dayType = (pd?.day_type ?? "unknown") as any;

        if (dayType === "working") {
          const primary = pickPrimaryTranche(pd.tranches ?? []);
          if (primary) {
            map.set(it.agent_id, {
              dayType: "working",
              trancheLabel: primary.nom,
              trancheColor: primary.color ?? null,
            });
          } else {
            map.set(it.agent_id, { dayType: "working" });
          }
        } else {
          map.set(it.agent_id, { dayType });
        }
      }

      return map;
    },
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  );

  return {
    statusByAgentId: swr.data,
    isLoading: swr.isLoading,
    error: swr.error,
    refresh: () => swr.mutate(undefined, { revalidate: true }),
  };
}
