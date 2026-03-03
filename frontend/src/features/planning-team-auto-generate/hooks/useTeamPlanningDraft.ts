"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { TeamPlanning as DraftTeamPlanningResponse } from "@/types/teamPlanning";

type TeamPlanningDraftKey = readonly ["teamPlanningDraft", number];

function keyOf(draftId: number | null): TeamPlanningDraftKey | null {
  if (!draftId) return null;
  return ["teamPlanningDraft", draftId];
}

export function useTeamPlanningDraft(draftId: number | null) {
  const swr = useSWR<DraftTeamPlanningResponse, Error, TeamPlanningDraftKey | null>(
    keyOf(draftId),
    ([, id]) =>
      apiFetch<DraftTeamPlanningResponse>(
        backendPath(`/planning/drafts/${id}/team-planning`),
      ),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    },
  );

  const clearDraftCache = async () => {
    await swr.mutate(undefined, { revalidate: false });
  };

  return {
    ...swr,
    clearDraftCache,
  };
}

export type { DraftTeamPlanningResponse };
