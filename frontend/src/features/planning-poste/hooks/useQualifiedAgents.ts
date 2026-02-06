"use client";

import { useMemo } from "react";
import useSWR from "swr";

import type { Agent } from "@/types";
import { searchQualifications } from "@/services/qualifications.service";
import { useAgents } from "@/features/agents/hooks/useAgents";

export function useQualifiedAgents(posteId: number | null) {
  const agents = useAgents();

  const qualifs = useSWR(
    posteId ? ["qualifications", "poste", posteId] : null,
    () => searchQualifications({ poste_id: posteId! }),
    { revalidateOnFocus: false, keepPreviousData: true }
  );

  const qualifiedAgents: Agent[] = useMemo(() => {
    if (!posteId) return [];
    if (!agents.data || !qualifs.data) return [];

    const byId = new Map<number, Agent>(agents.data.map((a) => [a.id, a]));

    return qualifs.data
      .map((q) => byId.get(q.agent_id))
      .filter((a): a is Agent => !!a);
  }, [posteId, agents.data, qualifs.data]);

  return {
    agents: qualifiedAgents,
    isLoading: agents.isLoading || qualifs.isLoading,
    error: agents.error ?? qualifs.error ?? null,
  };
}
