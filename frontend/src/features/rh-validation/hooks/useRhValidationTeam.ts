"use client";

import * as React from "react";
import useSWR from "swr";
import type { RhViolation } from "@/types/rhValidation";
import { rhValidationTeamKey } from "../swr/rhValidation.key";
import { rhValidationTeamFetcher } from "../swr/rhValidation.fetcher";
import type { RhValidateTeamResponse } from "@/types/rhValidation";

function flattenViolations(data: RhValidateTeamResponse | undefined): RhViolation[] {
  if (!data) return [];
  return data.results.flatMap((r) => r.result.violations ?? []);
}

export function useRhValidationTeam(params: {
  teamId: number | null;
  startDate: string | null;
  endDate: string | null;
  profile?: "fast" | "full";
  enabled?: boolean;
}) {
  const { teamId, startDate, endDate, profile = "full", enabled = true } = params;

  const key = enabled ? rhValidationTeamKey(teamId, startDate, endDate, profile) : null;

  const { data, error, isLoading, isValidating, mutate } = useSWR(key, rhValidationTeamFetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 30_000,
    keepPreviousData: true,
  });

  // stats globales
  const violations = React.useMemo(() => flattenViolations(data), [data]);

  const counts = React.useMemo(() => {
    const info = violations.filter((v) => v.severity === "info").length;
    const warning = violations.filter((v) => v.severity === "warning").length;
    const err = violations.filter((v) => v.severity === "error").length;
    return { info, warning, error: err, total: violations.length };
  }, [violations]);

  const perAgent = React.useMemo(() => {
    const rows = data?.results ?? [];
    return rows.map((r) => ({
      agent_id: r.agent_id,
      is_valid: r.result.is_valid,
      violations: r.result.violations ?? [],
      counts: {
        info: (r.result.violations ?? []).filter((v) => v.severity === "info").length,
        warning: (r.result.violations ?? []).filter((v) => v.severity === "warning").length,
        error: (r.result.violations ?? []).filter((v) => v.severity === "error").length,
        total: (r.result.violations ?? []).length,
      },
    }));
  }, [data]);

  const summary = React.useMemo(() => {
    const rows = data?.results ?? [];
    const valid = rows.filter((r) => r.result.is_valid).length;
    const invalid = rows.length - valid;
    const skipped = data?.skipped?.length ?? 0;
    return { valid, invalid, total: rows.length, skipped };
  }, [data]);

  return {
    data,
    results: data?.results ?? [],
    skipped: data?.skipped ?? [],

    // global
    violations,
    counts,
    summary,

    // per agent (pratique pour UI)
    perAgent,

    isLoading,
    isValidating,
    error,
    refresh: () => mutate(),
  };
}
