// src/utils/date.format.ts

function toISODate(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

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
