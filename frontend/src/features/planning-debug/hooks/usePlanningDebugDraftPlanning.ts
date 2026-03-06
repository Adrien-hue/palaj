"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";
import type { TeamPlanning } from "@/types/teamPlanning";

function keyOf(draftId: number | null | undefined) {
  if (!draftId) return null;
  return ["planningDebug", "draft", draftId] as const;
}

export function usePlanningDebugDraftPlanning(draftId: number | null | undefined) {
  return useSWR<TeamPlanning, Error, ReturnType<typeof keyOf>>(
    keyOf(draftId),
    ([, , id]) => apiFetch<TeamPlanning>(backendPath(`/planning/drafts/${id}/team-planning`)),
    {
      revalidateOnFocus: false,
    },
  );
}
