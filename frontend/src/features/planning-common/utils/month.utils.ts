// src/features/planning-common/utils/month.utils.ts

import { addDaysISO } from "@/utils/date.format";
import { isoWeekRangeFrom } from "@/features/planning-common/utils/planning.utils";

function toISO(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function monthGridRangeFrom(anchorISO: string): { start: string; end: string } {
  const d = new Date(anchorISO + "T00:00:00");
  const first = new Date(d.getFullYear(), d.getMonth(), 1);
  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0);

  const start = isoWeekRangeFrom(toISO(first)).start;
  const end = isoWeekRangeFrom(toISO(last)).end;
  return { start, end };
}

export function buildDaysRange(start: string, end: string): string[] {
  const out: string[] = [];
  let cur = start;
  while (cur <= end) {
    out.push(cur);
    cur = addDaysISO(cur, 1);
  }
  return out;
}

export function isInSameMonth(dayISO: string, anchorISO: string): boolean {
  return dayISO.slice(0, 7) === anchorISO.slice(0, 7);
}

export function monthLabelFR(anchorISO: string): string {
  const d = new Date(anchorISO + "T00:00:00");
  const label = new Intl.DateTimeFormat("fr-FR", { month: "long", year: "numeric" }).format(d);
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function monthAnchorISO(anchorISO: string): string {
  return anchorISO.slice(0, 7) + "-01";
}

export function addMonthsISO(anchorISO: string, deltaMonths: number): string {
  const d = new Date(monthAnchorISO(anchorISO) + "T00:00:00");
  d.setMonth(d.getMonth() + deltaMonths);
  return toISO(new Date(d.getFullYear(), d.getMonth(), 1));
}
