import type { AgentDay, Tranche } from "@/types";

export function parseTimeToMinutes(t: string): number {
  const [hhS, mmS] = t.split(":");
  const hh = Number(hhS);
  const mm = Number(mmS);

  // accepte 24:00:00
  if (hh === 24) return 24 * 60;

  return hh * 60 + mm;
}

export function trancheDurationMinutes(tranche: Tranche): number {
  const start = parseTimeToMinutes(tranche.heure_debut);
  const end = parseTimeToMinutes(tranche.heure_fin);
  return Math.max(0, end - start);
}

export function dayTotalMinutes(day: AgentDay): number {
  return day.tranches.reduce((acc, t) => acc + trancheDurationMinutes(t), 0);
}

export function formatMinutes(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${h}h${String(m).padStart(2, "0")}`;
}

export function formatDayShortFR(isoDate: string): string {
  // "2026-01-01" -> "jeu. 01/01"
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "2-digit" });
}

export function addDaysISO(isoDate: string, deltaDays: number): string {
  const d = new Date(isoDate + "T00:00:00");
  d.setDate(d.getDate() + deltaDays);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

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
