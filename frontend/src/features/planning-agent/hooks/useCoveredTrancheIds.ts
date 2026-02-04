// useCoveredTrancheIds.ts
"use client";

import { useCallback } from "react";
import useSWR from "swr";
import { getPosteCoverageForDay } from "@/services/poste-coverage.service";

export function useCoveredTrancheIds(params: {
  dateISO: string | null;
  posteIds: number[];
}) {
  const { dateISO, posteIds } = params;
  const shouldFetch = !!dateISO && posteIds.length > 0;

  const swr = useSWR(
    shouldFetch ? ["covered-tranches", dateISO, ...posteIds] : null,
    async () => {
      const results = await Promise.all(
        posteIds.map((posteId) => getPosteCoverageForDay(posteId, dateISO!))
      );

      const covered = new Set<number>();
      for (const dto of results) {
        for (const t of dto.tranches) {
          if (t.required_count > 0 && t.assigned_count >= t.required_count) {
            covered.add(t.tranche_id);
          }
        }
      }
      return covered;
    },
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );

  const refreshCoverage = useCallback(() => {
    return swr.mutate(undefined, { revalidate: true });
  }, [swr]);

  return {
    coveredTrancheIds: swr.data ?? new Set<number>(),
    isLoading: swr.isLoading,
    error: swr.error,
    refreshCoverage,
  };
}
