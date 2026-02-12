import { isWithinInterval, parseISO } from "date-fns";
import type { RhViolation } from "@/types/rhValidation";

export function rhViolationCoversDay(v: RhViolation, dayISO: string): boolean {
  // dayISO: "YYYY-MM-DD"
  const day = parseISO(`${dayISO}T00:00:00`);

  // priorité aux dates jour si fournies
  if (v.start_date && v.end_date) {
    const start = parseISO(`${v.start_date}T00:00:00`);
    const end = parseISO(`${v.end_date}T23:59:59`);
    return isWithinInterval(day, { start, end });
  }

  // fallback datetimes
  if (v.start_dt && v.end_dt) {
    const start = parseISO(v.start_dt);
    const end = parseISO(v.end_dt);
    return isWithinInterval(day, { start, end });
  }

  return false;
}
