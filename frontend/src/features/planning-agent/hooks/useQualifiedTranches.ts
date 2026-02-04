// src/features/planning-agent/hooks/useQualifiedTranches.ts
"use client";

import useSWR from "swr";
import { searchQualifications } from "@/services/qualifications.service";
import { listTranchesForPoste } from "@/services/tranches.service";
import type { Tranche } from "@/types";

export function useQualifiedTranches(agentId: number) {
  const {
    data: qualifications,
    isLoading: loadingQualifs,
    error: errorQualifs,
  } = useSWR(["qualifications", agentId], () => searchQualifications({agent_id: agentId}));
  console.debug("useQualifiedTranches - agentId:", agentId);
  const posteIds = (qualifications ?? []).map((q) => q.poste_id);

  const {
    data: tranchesByPoste,
    isLoading: loadingTranches,
    error: errorTranches,
  } = useSWR(
    posteIds.length ? ["qualified-tranches", ...posteIds] : null,
    async () => {
      const results = await Promise.all(posteIds.map((id) => listTranchesForPoste(id)));
      return results;
    }
  );

  const tranches: Tranche[] = (tranchesByPoste ?? []).flat();

  return {
    tranches,
    isLoading: loadingQualifs || loadingTranches,
    error: errorQualifs || errorTranches,
    posteIds,
  };
}
