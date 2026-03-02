"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { PlanningGenerateJobStatusResponse } from "./useTeamPlanningGenerate";

type TeamPlanningGenerateJobKey = readonly ["/planning/generate", string];

function keyOf(jobId: string | null): TeamPlanningGenerateJobKey | null {
  if (!jobId) return null;
  return ["/planning/generate", jobId];
}

function isRunningStatus(status?: PlanningGenerateJobStatusResponse["status"]) {
  return status === "queued" || status === "running";
}

export function useTeamPlanningGenerateJob(jobId: string | null) {
  const swr = useSWR<PlanningGenerateJobStatusResponse, Error, TeamPlanningGenerateJobKey | null>(
    keyOf(jobId),
    ([, id]) => apiFetch<PlanningGenerateJobStatusResponse>(backendPath(`/planning/generate/${id}`)),
    {
      revalidateOnFocus: true,
      refreshWhenHidden: false,
      refreshWhenOffline: false,
      dedupingInterval: 800,
      refreshInterval: (data) => {
        if (!jobId) return 0;
        return isRunningStatus(data?.status) ? 2000 : 0;
      },
    },
  );

  const clearJobCache = async () => {
    await swr.mutate(undefined, { revalidate: false });
  };

  return {
    ...swr,
    clearJobCache,
  };
}
