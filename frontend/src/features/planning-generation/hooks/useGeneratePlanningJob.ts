"use client";

import useSWRMutation from "swr/mutation";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import { DEFAULT_GENERATE_PARAMS } from "../constants";

export type JobStatus = "queued" | "running" | "success" | "failed";

export type PlanningGeneratePayload = {
  team_id: number;
  start_date: string;
  end_date: string;
};

export type PlanningGenerateRequest = PlanningGeneratePayload & typeof DEFAULT_GENERATE_PARAMS;

export type PlanningGenerateResponse = {
  job_id: string;
  draft_id: number;
  status: Extract<JobStatus, "queued">;
};

async function postGenerate(_key: string, { arg }: { arg: PlanningGeneratePayload }) {
  const body: PlanningGenerateRequest = {
    ...arg,
    ...DEFAULT_GENERATE_PARAMS,
  };

  return apiFetch<PlanningGenerateResponse>(backendPath("/planning/generate"), {
    method: "POST",
    body,
  });
}

export function useGeneratePlanningJob() {
  return useSWRMutation("/planning/generate", postGenerate);
}
