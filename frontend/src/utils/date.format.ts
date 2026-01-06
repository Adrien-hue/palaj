export function formatDateFR(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(d);
}
