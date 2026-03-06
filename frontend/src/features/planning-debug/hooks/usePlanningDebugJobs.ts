"use client";

import useSWR from "swr";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { DebugJobStatus } from "./usePlanningDebugGenerate";

export type PlanningDebugJobListItem = {
  job_id: string;
  team_id?: number;
  team_name?: string;
  start_date?: string;
  end_date?: string;
  status: DebugJobStatus;
  created_at?: string;
  draft_id?: number | null;
};

type JobsListResponse =
  | PlanningDebugJobListItem[]
  | {
      items?: PlanningDebugJobListItem[];
      jobs?: PlanningDebugJobListItem[];
    };

type PlanningDebugJobsKey = readonly [
  "planningDebug",
  "jobs",
  {
    q?: string;
    status?: string;
    team_id?: number;
  },
];

function keyOf(filters: { q?: string; status?: string; team_id?: number }) {
  return ["planningDebug", "jobs", filters] as const;
}

function normalizeJobsResponse(payload: JobsListResponse): PlanningDebugJobListItem[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.items)) return payload.items;
  if (Array.isArray(payload.jobs)) return payload.jobs;
  return [];
}

export function usePlanningDebugJobs(filters: { q?: string; status?: string; team_id?: number }) {
  return useSWR<PlanningDebugJobListItem[], Error, PlanningDebugJobsKey>(
    keyOf(filters),
    async ([, , localFilters]) => {
      const params = new URLSearchParams();
      if (localFilters.q) params.set("q", localFilters.q);
      if (localFilters.status) params.set("status", localFilters.status);
      if (localFilters.team_id != null) params.set("team_id", String(localFilters.team_id));

      const query = params.toString();
      const path = backendPath(`/planning/generate/jobs${query ? `?${query}` : ""}`);
      const response = await apiFetch<JobsListResponse>(path);
      return normalizeJobsResponse(response);
    },
    {
      keepPreviousData: true,
      revalidateOnFocus: false,
      dedupingInterval: 1000,
    },
  );
}
