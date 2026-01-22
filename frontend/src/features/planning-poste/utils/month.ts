function pad2(n: number) {
  return String(n).padStart(2, "0");
}

export function monthAnchorISO(dateISO: string) {
  // YYYY-MM-DD -> YYYY-MM-01
  return dateISO.slice(0, 7) + "-01";
}

export function addMonthsISO(anchorISO: string, delta: number) {
  const y = Number(anchorISO.slice(0, 4));
  const m = Number(anchorISO.slice(5, 7)) - 1;
  const d = new Date(y, m, 1);
  d.setMonth(d.getMonth() + delta);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-01`;
}

export function monthLabelFR(anchorISO: string) {
  const d = new Date(anchorISO + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", { month: "long", year: "numeric" })
    .format(d)
    .replace(/^\w/, (c) => c.toUpperCase());
}

export function buildMonthDays(anchorISO: string) {
  const y = Number(anchorISO.slice(0, 4));
  const m = Number(anchorISO.slice(5, 7));
  const last = new Date(y, m, 0).getDate();
  return Array.from({ length: last }, (_, i) => {
    const day = i + 1;
    return `${y}-${pad2(m)}-${pad2(day)}`;
  });
}

export function isoWeekRangeFrom(dateISO: string) {
  const d = new Date(dateISO + "T00:00:00");
  const day = (d.getDay() + 6) % 7; // Mon=0..Sun=6
  const start = new Date(d);
  start.setDate(d.getDate() - day);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  const toISO = (x: Date) =>
    `${x.getFullYear()}-${pad2(x.getMonth() + 1)}-${pad2(x.getDate())}`;

  return { start: toISO(start), end: toISO(end) };
}

export function isSameMonth(dateISO: string, anchorISO: string) {
  return dateISO.slice(0, 7) === anchorISO.slice(0, 7);
}
