export function formatDateFR(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "2-digit",
  }).format(d);
}
