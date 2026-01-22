// src/features/planning-common/utils/planning.utils.ts

import type { AgentDay, Tranche } from "@/types";
import { addDaysISO } from "@/utils/date.format";
import { timeToMinutes } from "@/utils/time.format";

/**
 * Semaine ISO (lundi -> dimanche) à partir d'une date ISO.
 */
export function isoWeekRangeFrom(isoDate: string): { start: string; end: string } {
  const d = new Date(isoDate + "T00:00:00");
  const day = d.getDay(); // 0=dim, 1=lun...
  const diffToMonday = (day === 0 ? -6 : 1) - day;
  d.setDate(d.getDate() + diffToMonday);

  const start = toISODate(d);
  const end = addDaysISO(start, 6);
  return { start, end };
}

function toISODate(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function trancheDurationMinutes(tranche: Tranche): number {
  const start = timeToMinutes(tranche.heure_debut);
  const end = timeToMinutes(tranche.heure_fin);
  return Math.max(0, end - start);
}

export function dayTotalMinutes(day: AgentDay): number {
  return day.tranches.reduce((acc, t) => acc + trancheDurationMinutes(t), 0);
}
