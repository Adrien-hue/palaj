"use client";

import * as React from "react";
import useSWR from "swr";
import type { RhViolation } from "@/types/rhValidation";
import { rhValidationAgentKey } from "../swr/rhValidation.key";
import { rhValidationAgentFetcher } from "../swr/rhValidation.fetcher";
import { buildRhDayIndex } from "@/features/rh-validation/utils/buildRhDayIndex";

export function useRhValidationAgent(params: {
  agentId: number | null;
  startDate: string | null;
  endDate: string | null;
  enabled?: boolean;
}) {
  const { agentId, startDate, endDate, enabled = true } = params;

  const key = enabled ? rhValidationAgentKey(agentId, startDate, endDate) : null;

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    rhValidationAgentFetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 30_000,
      keepPreviousData: true,
    },
  );

  const violations: RhViolation[] = data?.violations ?? [];

  const counts = {
    info: violations.filter((v) => v.severity === "info").length,
    warning: violations.filter((v) => v.severity === "warning").length,
    error: violations.filter((v) => v.severity === "error").length,
    total: violations.length,
  };

  const dayIndex = React.useMemo(() => {
    if (!startDate || !endDate) return {};
    return buildRhDayIndex({
      startDateISO: startDate,
      endDateISO: endDate,
      violations,
    });
  }, [startDate, endDate, violations]);

  return {
    data,
    isValid: data?.is_valid ?? null,
    violations,
    counts,
    isLoading,
    isValidating,
    error,
    dayIndex,
    refresh: () => mutate(),
  };
}
