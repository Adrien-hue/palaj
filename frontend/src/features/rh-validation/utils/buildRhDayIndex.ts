import { eachDayOfInterval, format, parseISO } from "date-fns";
import type { RhViolation } from "@/types/rhValidation";
import { rhViolationCoversDay } from "./rhViolationCoversDay";

export type RhDayIndex = Record<string, RhViolation[]>; // key = YYYY-MM-DD

export function buildRhDayIndex(params: {
  startDateISO: string;
  endDateISO: string;
  violations: RhViolation[];
}): RhDayIndex {
  const { startDateISO, endDateISO, violations } = params;

  const days = eachDayOfInterval({
    start: parseISO(`${startDateISO}T00:00:00`),
    end: parseISO(`${endDateISO}T00:00:00`),
  });

  const index: RhDayIndex = {};
  for (const d of days) {
    const dayISO = format(d, "yyyy-MM-dd");
    index[dayISO] = [];
  }

  for (const v of violations) {
    for (const d of days) {
      const dayISO = format(d, "yyyy-MM-dd");
      if (rhViolationCoversDay(v, dayISO)) index[dayISO]!.push(v);
    }
  }

  return index;
}
