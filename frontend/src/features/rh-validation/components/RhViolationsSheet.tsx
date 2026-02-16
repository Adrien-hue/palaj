"use client";

import * as React from "react";
import { differenceInCalendarDays } from "date-fns";
import type { RhViolation } from "@/types";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

import { formatDateFRLong } from "@/utils/date.format";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";

import { RhViolationCard } from "@/features/rh-validation/components/RhViolationCard";
import { groupRhViolations, type Severity } from "@/features/rh-validation/utils/rhViolations.group";

type Counts = { info: number; warning: number; error: number; total: number };

function matchesQuery(v: RhViolation, q: string) {
  if (!q) return true;
  const hay = `${v.code ?? ""} ${v.rule ?? ""} ${v.message ?? ""}`.toLowerCase();
  return hay.includes(q.toLowerCase());
}

function triggerVariantFor(counts: Pick<Counts, "error" | "warning">, disabled: boolean) {
  if (disabled) return "secondary" as const;
  if (counts.error > 0) return "destructive" as const;
  if (counts.warning > 0) return "secondary" as const;
  return "outline" as const;
}

function headerBadgeText(counts: Counts) {
  if (counts.error > 0) return `${counts.error} erreur(s)`;
  if (counts.warning > 0) return `${counts.warning} alerte(s)`;
  if (counts.total > 0) return "OK";
  return "—";
}

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
  counts: Counts;
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
      .filter((v) => show[(v.severity as Severity) ?? "info"])
      .filter((v) => matchesQuery(v, query));
  }, [violations, show, query]);

  const groups = React.useMemo(() => groupRhViolations(filtered), [filtered]);

  const buttonLabel = loading ? "Contrôle RH…" : "Contrôle RH";
  const btnVariant = triggerVariantFor({ error: counts.error, warning: counts.warning }, disabled);

  return (
    <>
      <Button
        type="button"
        size="sm"
        variant={btnVariant}
        disabled={disabled}
        onClick={() => setOpen(true)}
        className="w-full sm:w-auto"
      >
        {buttonLabel}
        <Badge variant="outline" className="ml-2 h-5 rounded-full px-2 py-0 text-[10px] tabular-nums">
          {headerBadgeText(counts)}
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
              <Button size="sm" variant={show.error ? "default" : "outline"} onClick={() => toggle("error")}>
                Bloquants
                <Badge variant="outline" className="ml-2 h-5 rounded-full px-2 py-0 text-[10px] tabular-nums">
                  {counts.error}
                </Badge>
              </Button>

              <Button size="sm" variant={show.warning ? "default" : "outline"} onClick={() => toggle("warning")}>
                Alertes
                <Badge variant="outline" className="ml-2 h-5 rounded-full px-2 py-0 text-[10px] tabular-nums">
                  {counts.warning}
                </Badge>
              </Button>

              <Button size="sm" variant={show.info ? "default" : "outline"} onClick={() => toggle("info")}>
                Infos
                <Badge variant="outline" className="ml-2 h-5 rounded-full px-2 py-0 text-[10px] tabular-nums">
                  {counts.info}
                </Badge>
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
        empty={<div className="p-6 text-sm text-muted-foreground">Aucune violation RH sur la période.</div>}
        bodyClassName="px-4 pb-4"
        contentClassName="w-full p-0 sm:max-w-lg"
      >
        <div className="space-y-3 p-4 pt-0">
          {groups.length === 0 ? (
            <div className="text-sm text-muted-foreground">Aucune violation selon les filtres.</div>
          ) : (
            <div className="space-y-3">
              {groups.map((g) => {
                const startISO = g.range.start ?? null;
                const endISO = g.range.end ?? null;

                let dayCount: number | null = null;
                if (startISO && endISO) {
                  dayCount =
                    differenceInCalendarDays(
                      new Date(endISO + "T00:00:00"),
                      new Date(startISO + "T00:00:00"),
                    ) + 1;
                }
                const isRange = dayCount !== null && dayCount > 1;

                const title = (g.rule && g.rule.trim().length > 0 ? g.rule : g.code) ?? "Violation";

                const rangeLabel = isRange && dayCount
                  ? `${g.range.label} · ${dayCount} jours`
                  : g.range.label;

                return (
                  <div key={g.key} className="space-y-2">
                    <RhViolationCard
                      severity={g.severity}
                      title={title}
                      message={g.message}
                      rangeLabel={rangeLabel}
                      count={g.count}
                    />

                    {onJumpToDate ? (
                      <div className="flex flex-wrap items-center gap-2">
                        {startISO ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              onJumpToDate(startISO);
                              setOpen(false);
                            }}
                          >
                            Aller au début
                          </Button>
                        ) : null}

                        {endISO && endISO !== startISO ? (
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
                    ) : null}
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
