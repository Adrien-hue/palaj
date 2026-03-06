"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { DebugJobStatus } from "./usePlanningDebugGenerate";

export type PlanningDebugJobResponse = {
  job_id: string;
  draft_id?: number | null;
  status: DebugJobStatus;
  progress?: number;
  solver_version?: string;
  verbosity?: string | number;
  time_limit_seconds?: number;
  solve_wall_time_seconds?: number;
  model_build_wall_time_seconds?: number;
  result_stats?: {
    stats?: Record<string, unknown>;
    [key: string]: unknown;
  } | null;
  error?: string | null;
  [key: string]: unknown;
};

type PlanningDebugJobKey = readonly ["planningDebug", "job", string];

function keyOf(jobId: string | null | undefined): PlanningDebugJobKey | null {
  if (!jobId) return null;
  return ["planningDebug", "job", jobId];
}

export function usePlanningDebugJob(jobId: string | null | undefined, autoRefresh = true) {
  return useSWR<PlanningDebugJobResponse, Error, PlanningDebugJobKey | null>(
    keyOf(jobId),
    ([, , id]) => apiFetch<PlanningDebugJobResponse>(backendPath(`/planning/generate/${id}`)),
    {
      refreshInterval: (currentData) => {
        if (!autoRefresh) return 0;
        const status = currentData?.status;
        return status === "queued" || status === "running" ? 1500 : 0;
      },
      refreshWhenHidden: false,
      dedupingInterval: 500,
      revalidateOnFocus: true,
    },
  );
}
