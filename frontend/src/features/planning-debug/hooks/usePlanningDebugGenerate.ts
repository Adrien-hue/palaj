"use client";

import useSWRMutation from "swr/mutation";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import { DEFAULT_DEBUG_GENERATE_PARAMS, type DebugGenerateParams } from "../constants";

export type DebugJobStatus = "queued" | "running" | "success" | "failed";

export type PlanningDebugGeneratePayload = {
  team_id: number;
  start_date: string;
  end_date: string;
};

export type PlanningDebugGenerateRequest = PlanningDebugGeneratePayload & DebugGenerateParams;

export type PlanningDebugGenerateResponse = {
  job_id: string;
  draft_id?: number | null;
  status: DebugJobStatus;
};

async function postGenerate(
  _key: string,
  { arg }: { arg: PlanningDebugGeneratePayload & Partial<DebugGenerateParams> },
) {
  const body: PlanningDebugGenerateRequest = {
    ...DEFAULT_DEBUG_GENERATE_PARAMS,
    ...arg,
  };

  return apiFetch<PlanningDebugGenerateResponse>(backendPath("/planning/generate"), {
    method: "POST",
    body,
  });
}

export function usePlanningDebugGenerate() {
  return useSWRMutation("/planning/debug/generate", postGenerate);
}
