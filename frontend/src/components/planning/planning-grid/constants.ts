import type { DayHeaderLabel, WeekStartsOn } from "./types";

const DAYS_MON_FIRST: DayHeaderLabel[] = [
  { short: "Lun", full: "Lundi" },
  { short: "Mar", full: "Mardi" },
  { short: "Mer", full: "Mercredi" },
  { short: "Jeu", full: "Jeudi" },
  { short: "Ven", full: "Vendredi" },
  { short: "Sam", full: "Samedi" },
  { short: "Dim", full: "Dimanche" },
];

export function getDaysHeader(weekStartsOn: WeekStartsOn): DayHeaderLabel[] {
  if (weekStartsOn === 1) return DAYS_MON_FIRST;

  // Sunday-first: rotate so Dim first
  const idx = DAYS_MON_FIRST.findIndex((d) => d.short === "Dim");
  return [...DAYS_MON_FIRST.slice(idx), ...DAYS_MON_FIRST.slice(0, idx)];
}
