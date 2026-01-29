// frontend/src/features/planning-common/period/usePlanningPeriodParam.ts
"use client";

import { useMemo, useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { PlanningPeriod } from "./period.types";
import { normalizeRange, shiftPlanningPeriod } from "./period.utils";

import { parseISODate, toISODate, startOfMonthDate } from "@/utils/date.format";

type NavMode = "push" | "replace";

export function usePlanningPeriodParam({ navMode = "push" }: { navMode?: NavMode } = {}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const period: PlanningPeriod = useMemo<PlanningPeriod>(() => {
    const startRaw = searchParams.get("start");
    const endRaw = searchParams.get("end");

    // range mode si start & end existent
    if (startRaw && endRaw) {
      const start = parseISODate(startRaw);
      const end = parseISODate(endRaw);
      return { kind: "range", ...normalizeRange(start, end) };
    }

    // month mode (compat) : anchor=YYYY-MM-01
    const anchorRaw = searchParams.get("anchor");
    const anchor = anchorRaw ? parseISODate(anchorRaw) : new Date();
    return { kind: "month", month: startOfMonthDate(anchor) };
  }, [searchParams]);

  const setPeriod = useCallback(
    (next: PlanningPeriod, mode: NavMode = navMode) => {
      const sp = new URLSearchParams(searchParams.toString());

      if (next.kind === "range") {
        sp.set("start", toISODate(next.start));
        sp.set("end", toISODate(next.end));
        sp.delete("anchor");
      } else {
        sp.set("anchor", toISODate(startOfMonthDate(next.month)));
        sp.delete("start");
        sp.delete("end");
      }

      const url = `${pathname}?${sp.toString()}`;
      mode === "replace" ? router.replace(url) : router.push(url);
    },
    [navMode, pathname, router, searchParams]
  );

  const step = useCallback(
    (dir: -1 | 1, mode: NavMode = navMode) => {
      setPeriod(shiftPlanningPeriod(period, dir), mode);
    },
    [navMode, period, setPeriod]
  );

  return { period, setPeriod, step };
}
