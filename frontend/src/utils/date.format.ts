// src/utils/date.format.ts

/** "YYYY-MM-DD" -> "DD/MM/YYYY" (FR) */
export function formatDateFR(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(d);
}

/** "YYYY-MM-DD" -> "jeudi 01 janvier 2026" (FR long) */
export function formatDateFRLong(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(d);
}

/** "YYYY-MM-DD" -> "jeu. 01/01" */
export function formatDayShortFR(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString("fr-FR", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
  });
}

/** "YYYY-MM-DD" + deltaDays -> "YYYY-MM-DD" */
export function addDaysISO(isoDate: string, deltaDays: number): string {
  const d = new Date(isoDate + "T00:00:00");
  d.setDate(d.getDate() + deltaDays);
  return toISODate(d);
}

/** "YYYY-MM-DD" -> Date (local, safe) */
export function parseISODate(isoDate: string): Date {
  return new Date(isoDate + "T00:00:00");
}

/** Date -> "YYYY-MM-DD" */
export function toISODate(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

/** Date + deltaDays */
export function addDays(date: Date, deltaDays: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + deltaDays);
  return d;
}

/** Lundi de la semaine courante */
export function startOfWeekMonday(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay(); // 0=dimanche
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function pad2(n: number) {
  return String(n).padStart(2, "0");
}

export function formatDayLabel(iso: string) {
  const d = parseISODate(iso);
  if (!d) return iso;
  // ex: "Mer 01/01"
  const wd = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"][d.getDay()];
  return `${wd} ${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`;
}

export function isWeekend(isoDate: string) {
  const dow = new Date(isoDate + "T00:00:00").getDay(); // 0=dim,6=sam
  return dow === 0 || dow === 6;
}