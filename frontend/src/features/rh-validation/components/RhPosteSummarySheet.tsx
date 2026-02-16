"use client";

import * as React from "react";

import type { RhDaySummary, RhRisk } from "@/types";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

import { cn } from "@/lib/utils";
import { formatDateFRLong } from "@/utils/date.format";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";

type RiskFilter = Exclude<RhRisk, "none"> | "none" | "any";

function riskRank(r: RhRisk) {
  return r === "high" ? 0 : r === "medium" ? 1 : r === "low" ? 2 : 3;
}

function riskLabel(r: RhRisk) {
  if (r === "high") return "Élevé";
  if (r === "medium") return "Moyen";
  if (r === "low") return "Faible";
  return "Aucun";
}

type Counters = {
  totalDays: number;
  high: number;
  medium: number;
  low: number;
  blockersDays: number;
  issuesDays: number;
  blockers: number;
  issues: number;
};

function computeCounters(days: RhDaySummary[] | undefined): Counters {
  const arr = days ?? [];
  let high = 0,
    medium = 0,
    low = 0,
    blockersDays = 0,
    issuesDays = 0,
    blockers = 0,
    issues = 0;

  for (const d of arr) {
    if (d.risk === "high") high++;
    else if (d.risk === "medium") medium++;
    else if (d.risk === "low") low++;

    const b = d.agents_with_blockers_count ?? 0;
    const i = d.agents_with_issues_count ?? 0;

    blockers += b;
    issues += i;

    if (b > 0) blockersDays++;
    if (i > 0) issuesDays++;
  }

  return {
    totalDays: arr.length,
    high,
    medium,
    low,
    blockersDays,
    issuesDays,
    blockers,
    issues,
  };
}

function matchesQuery(d: RhDaySummary, qRaw: string) {
  const q = qRaw.trim();
  if (!q) return true;

  const hay = [
    d.date,
    d.risk,
    ...(d.top_triggers ?? []).map((t) => `${t.key} ${t.severity} ${t.count}`),
  ]
    .join(" ")
    .toLowerCase();

  return hay.includes(q.toLowerCase());
}

function buttonVariantFor(days: RhDaySummary[] | undefined, disabled: boolean) {
  if (disabled) return "secondary" as const;
  const arr = days ?? [];
  if (arr.some((d) => (d.agents_with_blockers_count ?? 0) > 0))
    return "destructive" as const;
  if (
    arr.some(
      (d) =>
        (d.agents_with_issues_count ?? 0) > 0 ||
        d.risk === "high" ||
        d.risk === "medium",
    )
  )
    return "secondary" as const;
  return "outline" as const;
}

function sheetBadgeText(c: Counters) {
  if (c.totalDays === 0) return "—";
  if (c.blockers > 0) return `${c.blockers} bloquant(s)`;
  if (c.issues > 0) return `${c.issues} alerte(s)`;
  return "OK";
}

function daySeverityScore(args: { blockers: number; issues: number; risk: RhRisk }) {
  const { blockers, issues, risk } = args;
  // priorité: bloquants > alertes > risque > date
  if (blockers > 0) return 0;
  if (issues > 0) return 1;
  return 2 + riskRank(risk);
}

function dayCardClass(args: { blockers: number; issues: number; risk: RhRisk }) {
  const { blockers, issues, risk } = args;
  if (blockers > 0) return "border-destructive/35 bg-destructive/5";
  if (issues > 0) return "border-amber-500/30 bg-amber-500/5";
  if (risk === "high" || risk === "medium")
    return "border-muted-foreground/20 bg-muted/0";
  return "";
}

function DayRhBadge({
  blockers,
  issues,
}: {
  blockers: number;
  issues: number;
}) {
  if (blockers > 0) {
    return (
      <Badge
        variant="destructive"
        className="h-5 rounded-full px-2 py-0 text-[10px] tabular-nums"
        title={`${blockers} agent(s) bloquant(s)`}
      >
        Bloq. {blockers}
      </Badge>
    );
  }

  if (issues > 0) {
    return (
      <Badge
        variant="secondary"
        className="h-5 rounded-full px-2 py-0 text-[10px] tabular-nums"
        title={`${issues} agent(s) avec alerte(s)`}
      >
        Alertes {issues}
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className="h-5 rounded-full px-2 py-0 text-[10px]"
      title="Aucun signal RH"
    >
      OK
    </Badge>
  );
}

export function RhPosteSummarySheet({
  disabled = false,
  startDate,
  endDate,
  profileLabel,
  eligibleAgentsCount,
  days,
  loading = false,
  onJumpToDate,
}: {
  disabled?: boolean;
  startDate: string;
  endDate: string;

  profileLabel?: string;
  eligibleAgentsCount?: number;

  days: RhDaySummary[] | undefined;
  loading?: boolean;

  onJumpToDate?: (isoDate: string) => void;
}) {
  const [open, setOpen] = React.useState(false);

  const [risk, setRisk] = React.useState<RiskFilter>("any");
  const [onlyWithSignals, setOnlyWithSignals] = React.useState(false);
  const [query, setQuery] = React.useState("");

  const counters = React.useMemo(() => computeCounters(days), [days]);

  const filtered = React.useMemo(() => {
    const arr = (days ?? [])
      .map((d) => {
        const blockers = d.agents_with_blockers_count ?? 0;
        const issues = d.agents_with_issues_count ?? 0;
        return { d, blockers, issues };
      })
      .filter(({ d }) => (risk === "any" ? true : d.risk === risk))
      .filter(({ d, blockers, issues }) => {
        if (!onlyWithSignals) return true;
        // signal = bloquant OU alerte OU risque != none
        return blockers > 0 || issues > 0 || d.risk !== "none";
      })
      .filter(({ d }) => matchesQuery(d, query))
      .slice()
      .sort((a, b) => {
        const ra = daySeverityScore({ blockers: a.blockers, issues: a.issues, risk: a.d.risk });
        const rb = daySeverityScore({ blockers: b.blockers, issues: b.issues, risk: b.d.risk });
        if (ra !== rb) return ra - rb;
        return a.d.date.localeCompare(b.d.date);
      });

    return arr;
  }, [days, risk, onlyWithSignals, query]);

  const buttonLabel = loading ? "Contrôle RH…" : "Contrôle RH";
  const btnVariant = buttonVariantFor(days, disabled);
  const badgeText = sheetBadgeText(counters);

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
        <Badge
          variant="outline"
          className="ml-2 h-5 rounded-full px-2 py-0 text-[10px]"
        >
          {badgeText}
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
              {typeof eligibleAgentsCount === "number" ? (
                <span className="ml-2">
                  · {eligibleAgentsCount} agent(s) éligible(s)
                </span>
              ) : null}
              {profileLabel ? (
                <span className="ml-2">· Profil : {profileLabel}</span>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                variant={risk === "any" ? "default" : "outline"}
                onClick={() => setRisk("any")}
              >
                Tous
              </Button>

              <Button
                size="sm"
                variant={risk === "high" ? "default" : "outline"}
                onClick={() => setRisk("high")}
              >
                Élevé
                <Badge
                  variant="outline"
                  className="ml-2 h-5 rounded-full px-2 py-0 text-[10px]"
                >
                  {counters.high}
                </Badge>
              </Button>

              <Button
                size="sm"
                variant={risk === "medium" ? "default" : "outline"}
                onClick={() => setRisk("medium")}
              >
                Moyen
                <Badge
                  variant="outline"
                  className="ml-2 h-5 rounded-full px-2 py-0 text-[10px]"
                >
                  {counters.medium}
                </Badge>
              </Button>

              <Button
                size="sm"
                variant={risk === "low" ? "default" : "outline"}
                onClick={() => setRisk("low")}
              >
                Faible
                <Badge
                  variant="outline"
                  className="ml-2 h-5 rounded-full px-2 py-0 text-[10px]"
                >
                  {counters.low}
                </Badge>
              </Button>

              <Button
                size="sm"
                variant={risk === "none" ? "default" : "outline"}
                onClick={() => {
                  setRisk("none");
                  setOnlyWithSignals(false);
                }}
              >
                Aucun
              </Button>

              <Button
                size="sm"
                variant={onlyWithSignals ? "default" : "outline"}
                onClick={() => {
                  setOnlyWithSignals((v) => {
                    const next = !v;
                    if (next && risk === "none") setRisk("any");
                    return next;
                  });
                }}
              >
                Uniquement avec signaux
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setRisk("any");
                  setOnlyWithSignals(false);
                  setQuery("");
                }}
                className="ml-auto"
              >
                Réinitialiser
              </Button>

              <div className="w-full sm:w-auto text-xs text-muted-foreground">
                {filtered.length} jour(s) · {counters.blockersDays} jour(s)
                bloquant(s) · {counters.issuesDays} jour(s) avec alertes
              </div>
            </div>

            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher (date, trigger, risque)…"
            />
          </div>
        }
        isEmpty={(days?.length ?? 0) === 0}
        empty={
          <div className="p-6 text-sm text-muted-foreground">
            Aucun résultat RH sur la période.
          </div>
        }
        bodyClassName="px-4 pb-4"
        contentClassName="w-full p-0 sm:max-w-lg"
      >
        <div className="space-y-2 p-4 pt-0">
          {filtered.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Aucun jour selon les filtres.
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map(({ d, blockers, issues }) => {
                return (
                  <div
                    key={d.date}
                    className={cn(
                      "rounded-lg border p-3",
                      dayCardClass({ blockers, issues, risk: d.risk }),
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge
                            variant={d.risk === "high" || d.risk === "medium" ? "secondary" : "outline"}
                            className="h-5 rounded-full px-2 py-0 text-[10px]"
                            title={`Risque : ${riskLabel(d.risk)}`}
                          >
                            {riskLabel(d.risk).toUpperCase()}
                          </Badge>

                          <DayRhBadge blockers={blockers} issues={issues} />

                          <div className="text-xs text-muted-foreground">
                            {formatDateFRLong(d.date)}
                          </div>
                        </div>

                        {d.top_triggers?.length ? (
                          <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                            <div className="text-[11px] text-muted-foreground/80">
                              Déclencheurs principaux
                            </div>
                            <ul className="space-y-0.5">
                              {d.top_triggers.slice(0, 5).map((t) => (
                                <li
                                  key={t.key}
                                  className="flex items-center justify-between gap-2"
                                >
                                  <span className="truncate">{t.key}</span>
                                  <span className="tabular-nums text-muted-foreground/80">
                                    x{t.count}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : (
                          <div className="mt-2 text-xs text-muted-foreground">
                            Aucun déclencheur notable.
                          </div>
                        )}
                      </div>
                    </div>

                    {onJumpToDate ? (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            onJumpToDate(d.date);
                            setOpen(false);
                          }}
                        >
                          Aller au jour
                        </Button>
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
