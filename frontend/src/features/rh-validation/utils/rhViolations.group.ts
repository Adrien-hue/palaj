import type { RhViolation } from "@/types";
import { formatDateFRLong } from "@/utils/date.format";

export type Severity = "error" | "warning" | "info";

export type RhViolationGroup = {
  key: string;
  severity: Severity;
  code?: string | null;
  rule?: string | null;
  message: string;
  range: { start?: string | null; end?: string | null; label: string };
  count: number;
  items: RhViolation[];
};

function sevRank(s: Severity) {
  return s === "error" ? 0 : s === "warning" ? 1 : 2;
}

function isoDay(v: RhViolation, which: "start" | "end"): string | null {
  const date = which === "start" ? v.start_date : v.end_date;
  const dt = which === "start" ? v.start_dt : v.end_dt;
  return (date && date.slice(0, 10)) || (dt && dt.slice(0, 10)) || null;
}

function rangeKey(v: RhViolation) {
  const s = isoDay(v, "start") ?? "";
  const e = isoDay(v, "end") ?? "";
  return `${s}__${e}`;
}

function rangeLabel(v: RhViolation) {
  const s = isoDay(v, "start");
  const e = isoDay(v, "end");

  if (!s && !e) return "Plage inconnue";
  if (s && (!e || e === s)) return formatDateFRLong(s);
  return `${formatDateFRLong(s!)} → ${formatDateFRLong(e!)}`;
}

export function groupRhViolations(violations: RhViolation[] | undefined): RhViolationGroup[] {
  const arr = violations ?? [];
  const map = new Map<string, RhViolationGroup>();

  for (const v of arr) {
    const severity = (v.severity as Severity) ?? "info";
    const start = isoDay(v, "start");
    const end = isoDay(v, "end");

    const key = [severity, v.code ?? "", v.rule ?? "", v.message ?? "", rangeKey(v)].join("||");

    const existing = map.get(key);
    if (existing) {
      existing.items.push(v);
      existing.count++;
      continue;
    }

    map.set(key, {
      key,
      severity,
      code: v.code ?? null,
      rule: v.rule ?? null,
      message: v.message ?? "",
      range: { start, end, label: rangeLabel(v) },
      count: 1,
      items: [v],
    });
  }

  return Array.from(map.values()).sort((a, b) => {
    const r = sevRank(a.severity) - sevRank(b.severity);
    if (r !== 0) return r;

    const as = a.range.start ?? "";
    const bs = b.range.start ?? "";
    if (as !== bs) return as.localeCompare(bs);

    // stable : message ensuite
    return a.message.localeCompare(b.message);
  });
}
