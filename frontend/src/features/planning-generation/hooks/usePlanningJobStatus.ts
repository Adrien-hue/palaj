"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { JobStatus } from "./useGeneratePlanningJob";

export type PlanningJobStatusResponse = {
  job_id: string;
  draft_id: number;
  status: JobStatus;
  progress?: number;
  result_stats?: unknown;
  error?: string | null;
};

type PlanningJobStatusKey = readonly ["planningGeneration", "job", string];

function keyOf(jobId: string | null | undefined): PlanningJobStatusKey | null {
  if (!jobId) return null;
  return ["planningGeneration", "job", jobId];
}

export function usePlanningJobStatus(jobId: string | null | undefined) {
  return useSWR<PlanningJobStatusResponse, Error, PlanningJobStatusKey | null>(
    keyOf(jobId),
    ([, , id]) => apiFetch<PlanningJobStatusResponse>(backendPath(`/planning/generate/${id}`)),
    {
      refreshInterval: (currentData) => {
        const status = currentData?.status;
        return status === "queued" || status === "running" ? 1500 : 0;
      },
      refreshWhenHidden: false,
      dedupingInterval: 500,
      revalidateOnFocus: true,
    },
  );
}
