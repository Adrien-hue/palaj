"use client";

import * as React from "react";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";
import { ApiError } from "@/lib/api/errors";

export type ResultStats = {
  coverage_ratio?: number;
  score?: number;
  solve_time_seconds?: number;
  num_assignments?: number;
  soft_violations?: number;
  [key: string]: unknown;
};

export type PlanningGenerateRequest = {
  team_id: number;
  start_date: string;
  end_date: string;
  seed: number;
  time_limit_seconds: number;
};

export type PlanningGenerateResponse = {
  job_id: string;
  draft_id?: number;
  status: "queued";
};

export type JobStatus = "queued" | "running" | "success" | "failed";

export type PlanningGenerateJobStatusResponse = {
  job_id: string;
  draft_id?: number;
  status: JobStatus;
  progress?: number;
  result_stats?: ResultStats;
  solver_status?: string;
  error?: unknown;
  [key: string]: unknown;
};

export function useTeamPlanningGenerate() {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<ApiError | Error | null>(null);
  const controllerRef = React.useRef<AbortController | null>(null);

  const submit = React.useCallback(async (payload: PlanningGenerateRequest) => {
    setIsSubmitting(true);
    setError(null);

    // Anti-race: on annule la requête précédente avant de lancer la suivante.
    // Couplé au token côté page, cela évite qu'une réponse tardive écrase l'état courant.
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      return await apiFetch<PlanningGenerateResponse>(backendPath("/planning/generate"), {
        method: "POST",
        body: payload,
        signal: controller.signal,
      });
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        throw err;
      }
      setError(err instanceof Error ? err : new Error("Erreur inconnue"));
      throw err;
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
        setIsSubmitting(false);
      }
    }
  }, []);

  React.useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  return {
    submit,
    isSubmitting,
    error,
  };
}
