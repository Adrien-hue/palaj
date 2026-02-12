"use client";

import * as React from "react";
import { differenceInCalendarDays } from "date-fns";
import type { RhViolation } from "@/types";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

import { cn } from "@/lib/utils";
import { formatDateFRLong } from "@/utils/date.format";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";

type Severity = "error" | "warning" | "info";

function sevRank(s: Severity) {
  return s === "error" ? 0 : s === "warning" ? 1 : 2;
}

function sevBadgeVariant(
  sev: Severity,
): React.ComponentProps<typeof Badge>["variant"] {
  if (sev === "error") return "destructive";
  if (sev === "warning") return "secondary";
  return "outline";
}

function matchesQuery(v: RhViolation, q: string) {
  if (!q) return true;
  const hay =
    `${v.code ?? ""} ${v.rule ?? ""} ${v.message ?? ""}`.toLowerCase();
  return hay.includes(q.toLowerCase());
}

function triggerVariantFor(
  counts: { error: number; warning: number },
  disabled: boolean,
) {
  if (disabled) return "secondary" as const;
  if (counts.error > 0) return "destructive" as const;
  return "secondary" as const;
}

function rangeKey(v: RhViolation) {
  // On privilégie les dates "jour" (stables) ; fallback sur dt si besoin
  const s =
    (v.start_date && v.start_date.slice(0, 10)) ||
    (v.start_dt && v.start_dt.slice(0, 10)) ||
    "";
  const e =
    (v.end_date && v.end_date.slice(0, 10)) ||
    (v.end_dt && v.end_dt.slice(0, 10)) ||
    "";
  return `${s}__${e}`;
}

function rangeLabel(v: RhViolation) {
  const s =
    (v.start_date && v.start_date.slice(0, 10)) ||
    (v.start_dt && v.start_dt.slice(0, 10)) ||
    null;
  const e =
    (v.end_date && v.end_date.slice(0, 10)) ||
    (v.end_dt && v.end_dt.slice(0, 10)) ||
    null;

  if (!s && !e) return "Plage inconnue";
  if (s && (!e || e === s)) return formatDateFRLong(s);
  return `${formatDateFRLong(s!)} → ${formatDateFRLong(e!)}`;
}

type Group = {
  key: string;
  severity: Severity;
  code?: string | null;
  rule?: string | null;
  message: string;
  range: { start?: string | null; end?: string | null; label: string };
  items: RhViolation[];
};

export function RhViolationsSheet({
  disabled = false,
  startDate,
  endDate,
  violations,
  counts,
  loading = false,
  onJumpToDate,
}: {
  disabled?: boolean;
  startDate: string;
  endDate: string;
  violations: RhViolation[];
  counts: { info: number; warning: number; error: number; total: number };
  loading?: boolean;
  onJumpToDate?: (isoDate: string) => void;
}) {
  const [open, setOpen] = React.useState(false);

  const [show, setShow] = React.useState<Record<Severity, boolean>>({
    error: true,
    warning: true,
    info: false,
  });

  const [query, setQuery] = React.useState("");

  const toggle = (sev: Severity) => setShow((s) => ({ ...s, [sev]: !s[sev] }));

  const filtered = React.useMemo(() => {
    return (violations ?? [])
      .filter((v) => show[v.severity as Severity])
      .filter((v) => matchesQuery(v, query));
  }, [violations, show, query]);

  const groups = React.useMemo<Group[]>(() => {
    const map = new Map<string, Group>();

    for (const v of filtered) {
      const sev = v.severity as Severity;

      const s =
        (v.start_date && v.start_date.slice(0, 10)) ||
        (v.start_dt && v.start_dt.slice(0, 10)) ||
        null;
      const e =
        (v.end_date && v.end_date.slice(0, 10)) ||
        (v.end_dt && v.end_dt.slice(0, 10)) ||
        null;

      // clé de regroupement : même "problème", même plage
      const key = [
        sev,
        v.code ?? "",
        v.rule ?? "",
        v.message ?? "",
        rangeKey(v),
      ].join("||");

      const existing = map.get(key);
      if (existing) {
        existing.items.push(v);
      } else {
        map.set(key, {
          key,
          severity: sev,
          code: v.code ?? null,
          rule: v.rule ?? null,
          message: v.message ?? "",
          range: { start: s, end: e, label: rangeLabel(v) },
          items: [v],
        });
      }
    }

    return Array.from(map.values()).sort((a, b) => {
      const r = sevRank(a.severity) - sevRank(b.severity);
      if (r !== 0) return r;
      // ensuite par date de début
      const as = a.range.start ?? "";
      const bs = b.range.start ?? "";
      return as.localeCompare(bs);
    });
  }, [filtered]);

  const buttonLabel = loading ? "Contrôle RH…" : "Contrôle RH";

  return (
    <>
      <Button
        type="button"
        size="sm"
        variant={triggerVariantFor(counts, disabled)}
        disabled={disabled}
        onClick={() => setOpen(true)}
        className="w-full sm:w-auto"
      >
        {buttonLabel}

        <Badge
          variant="outline"
          className="ml-2 h-5 rounded-full px-2 py-0 text-[10px]"
        >
          {counts.error > 0
            ? `${counts.error} erreur(s)`
            : counts.warning > 0
              ? `${counts.warning} alerte(s)`
              : counts.total > 0
                ? "OK"
                : "—"}
        </Badge>
      </Button>

      <PlanningSheetShell
        open={open}
        onOpenChange={setOpen}
        headerVariant="sticky"
        title="Contrôle RH"
        description={
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              {formatDateFRLong(startDate)} → {formatDateFRLong(endDate)}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                variant={show.error ? "default" : "outline"}
                onClick={() => toggle("error")}
              >
                Erreurs
              </Button>
              <Button
                size="sm"
                variant={show.warning ? "default" : "outline"}
                onClick={() => toggle("warning")}
              >
                Alertes
              </Button>
              <Button
                size="sm"
                variant={show.info ? "default" : "outline"}
                onClick={() => toggle("info")}
              >
                Infos
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setShow({ error: true, warning: true, info: false });
                  setQuery("");
                }}
                className="ml-auto"
              >
                Réinitialiser
              </Button>

              <div className="w-full sm:w-auto text-xs text-muted-foreground">
                {filtered.length} affichée(s) · {groups.length} problème(s)
              </div>
            </div>

            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher (message, règle, code)…"
            />
          </div>
        }
        isEmpty={counts.total === 0}
        empty={
          <div className="p-6 text-sm text-muted-foreground">
            Aucune violation RH sur la période.
          </div>
        }
        bodyClassName="px-4 pb-4"
        contentClassName="w-full p-0 sm:max-w-lg"
      >
        <div className="space-y-3 p-4 pt-0">
          {groups.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Aucune violation selon les filtres.
            </div>
          ) : (
            <div className="space-y-3">
              {groups.map((g) => {
                const startISO = g.range.start ?? null;
                const endISO = g.range.end ?? null;

                let dayCount: number | null = null;

                if (startISO && endISO) {
                  const start = new Date(startISO + "T00:00:00");
                  const end = new Date(endISO + "T00:00:00");
                  dayCount = differenceInCalendarDays(end, start) + 1;
                }

                const isRange = dayCount !== null && dayCount > 1;

                return (
                  <div key={g.key} className="rounded-lg border p-3 bg-muted">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={sevBadgeVariant(g.severity)}
                            className={cn(
                              "h-5 rounded-full px-2 py-0 text-[10px]",
                            )}
                          >
                            {g.severity.toUpperCase()}
                          </Badge>

                          {isRange ? (
                            <Badge
                              variant="outline"
                              className="h-5 rounded-full px-2 py-0 text-[10px]"
                            >
                              {dayCount} jours
                            </Badge>
                          ) : null}

                          <div className="text-xs text-muted-foreground">
                            {g.range.label}
                          </div>

                          {g.items.length > 1 ? (
                            <Badge
                              variant="outline"
                              className="h-5 rounded-full px-2 py-0 text-[10px]"
                            >
                              x{g.items.length}
                            </Badge>
                          ) : null}
                        </div>

                        <div className="mt-2 text-sm leading-snug">
                          {g.message}
                        </div>
                        <div className="mt-1 text-[11px] text-muted-foreground">
                          {(g.rule && g.rule.trim().length > 0
                            ? g.rule
                            : g.code) ?? ""}
                        </div>
                      </div>
                    </div>

                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      {onJumpToDate && startISO ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            onJumpToDate(startISO);
                            setOpen(false); // optionnel : ferme la sheet
                          }}
                        >
                          Aller au début
                        </Button>
                      ) : null}

                      {onJumpToDate && endISO && endISO !== startISO ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            onJumpToDate(endISO);
                            setOpen(false);
                          }}
                        >
                          Aller à la fin
                        </Button>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </PlanningSheetShell>
    </>
  );
}
