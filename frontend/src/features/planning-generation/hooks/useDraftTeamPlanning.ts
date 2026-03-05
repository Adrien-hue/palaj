"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { TeamPlanning } from "@/types/teamPlanning";

function keyOf(draftId: number | null, enabled: boolean) {
  if (!draftId || !enabled) return null;
  return ["planningGeneration", "draft", draftId] as const;
}

export function useDraftTeamPlanning(draftId: number | null, enabled: boolean) {
  return useSWR<TeamPlanning, Error, ReturnType<typeof keyOf>>(
    keyOf(draftId, enabled),
    ([, , id]) => apiFetch<TeamPlanning>(backendPath(`/planning/drafts/${id}/team-planning`)),
    {
      keepPreviousData: true,
      revalidateOnFocus: false,
    },
  );
}
