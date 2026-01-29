// src/utils/date.format.ts
import { fr } from "date-fns/locale";
import {
  addDays as dfAddDays,
  addMonths as dfAddMonths,
  differenceInCalendarDays,
  endOfMonth,
  format,
  isWeekend as dfIsWeekend,
  parseISO,
  startOfMonth,
  startOfWeek,
} from "date-fns";

/** "YYYY-MM-DD" -> "DD/MM/YYYY" (FR) */
export function formatDateFR(isoDate: string): string {
  const d = parseISO(isoDate);
  return format(d, "dd/MM/yyyy", { locale: fr });
}

/** "YYYY-MM-DD" -> "jeudi 01 janvier 2026" (FR long) */
export function formatDateFRLong(isoDate: string): string {
  const d = parseISO(isoDate);
  // LLLL => month long in locale
  return format(d, "EEEE dd LLLL yyyy", { locale: fr });
}

/** "YYYY-MM-DD" -> "jeu. 01/01" */
export function formatDayShortFR(isoDate: string): string {
  const d = parseISO(isoDate);
  return format(d, "EEE dd/MM", { locale: fr });
}

/** "YYYY-MM-DD" + deltaDays -> "YYYY-MM-DD" */
export function addDaysISO(isoDate: string, deltaDays: number): string {
  const d = parseISO(isoDate);
  return toISODate(dfAddDays(d, deltaDays));
}

/** "YYYY-MM-DD" -> Date (safe) */
export function parseISODate(isoDate: string): Date {
  return parseISO(isoDate);
}

/** Date -> "YYYY-MM-DD" */
export function toISODate(d: Date): string {
  return format(d, "yyyy-MM-dd");
}

/** Date + deltaDays */
export function addDays(date: Date, deltaDays: number): Date {
  return dfAddDays(date, deltaDays);
}

/** Lundi de la semaine courante (weekStartsOn: 1) */
export function startOfWeekMonday(date: Date): Date {
  return startOfWeek(date, { weekStartsOn: 1 });
}

export function pad2(n: number) {
  return String(n).padStart(2, "0");
}

export function formatDayLabel(iso: string) {
  const d = parseISO(iso);
  // ex: "Mer 01/01"
  return format(d, "EEE dd/MM", { locale: fr });
}

export function isWeekend(isoDate: string) {
  return dfIsWeekend(parseISO(isoDate));
}

/** Helpers utiles pour la navigation de période (date-fns) */
export function startOfMonthDate(date: Date): Date {
  return startOfMonth(date);
}

export function endOfMonthDate(date: Date): Date {
  return endOfMonth(date);
}

export function addMonthsDate(date: Date, deltaMonths: number): Date {
  return dfAddMonths(date, deltaMonths);
}

export function diffDaysInclusive(start: Date, end: Date): number {
  return differenceInCalendarDays(end, start) + 1;
}
