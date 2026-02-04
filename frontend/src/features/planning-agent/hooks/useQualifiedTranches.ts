// src/features/planning-agent/hooks/useQualifiedTranches.ts
"use client";

import useSWR from "swr";
import { searchQualifications } from "@/services/qualifications.service";
import { listTranchesForPoste } from "@/services/tranches.service";
import type { Tranche } from "@/types";
import { useMemo } from "react";

export function useQualifiedTranches(agentId: number) {
  const {
    data: qualifications,
    isLoading: loadingQualifs,
    error: errorQualifs,
  } = useSWR(["qualifications", agentId], () =>
    searchQualifications({ agent_id: agentId }),
  );
  
  const posteIds = useMemo(() => {
    const ids = new Set<number>();
    for (const q of qualifications ?? []) ids.add(q.poste_id);
    return Array.from(ids).sort((a, b) => a - b);
  }, [qualifications]);

  const {
    data: tranchesByPoste,
    isLoading: loadingTranches,
    error: errorTranches,
  } = useSWR(
    posteIds.length ? ["qualified-tranches", ...posteIds] : null,
    async () => {
      const results = await Promise.all(
        posteIds.map((id) => listTranchesForPoste(id)),
      );
      return results;
    },
  );

  const tranches: Tranche[] = (tranchesByPoste ?? []).flat();

  return {
    tranches,
    isLoading: loadingQualifs || loadingTranches,
    error: errorQualifs || errorTranches,
    posteIds,
  };
}
