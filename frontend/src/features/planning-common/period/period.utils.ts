// frontend/src/features/planning-common/period/period.utils.ts

import type { PlanningPeriod } from "./period.types";
import {
  addDays,
  addMonthsDate,
  diffDaysInclusive,
  startOfMonthDate,
} from "@/utils/date.format";

function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function normalizeRange(a: Date, b: Date) {
  const A = startOfDay(a);
  const B = startOfDay(b);
  return A <= B ? { start: A, end: B } : { start: B, end: A };
}

export function shiftPlanningPeriod(p: PlanningPeriod, dir: -1 | 1): PlanningPeriod {
  if (p.kind === "month") {
    return { kind: "month", month: startOfMonthDate(addMonthsDate(p.month, dir)) };
  }

  const len = diffDaysInclusive(p.start, p.end);
  const delta = dir * len;
  return {
    kind: "range",
    start: addDays(p.start, delta),
    end: addDays(p.end, delta),
  };
}

export function monthToDefaultRange(month: Date): PlanningPeriod {
  const m = startOfMonthDate(month);
  return { kind: "range", start: m, end: addDays(m, 13) }; // 1..14
}

export function rangeToMonth(start: Date): PlanningPeriod {
  return { kind: "month", month: startOfMonthDate(start) };
}
