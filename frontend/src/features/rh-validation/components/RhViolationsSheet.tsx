"use client";

import * as React from "react";
import { differenceInCalendarDays } from "date-fns";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  OctagonAlert,
  RotateCcw,
  Search,
  TriangleAlert,
  User,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

import { formatDateFRLong } from "@/utils/date.format";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";

import { RhViolationCard } from "@/features/rh-validation/components/RhViolationCard";
import { groupRhViolations, type Severity } from "@/features/rh-validation/utils/rhViolations.group";
import type { RhViolationOccurrence } from "@/features/rh-validation/types";

type Counts = { info: number; warning: number; error: number; total: number };
type AgentBadge = { id: number; label: string };

const DEFAULT_SHOW: Record<Severity, boolean> = {
  error: true,
  warning: true,
  info: false,
};

const COUNT_PILL_CLASS =
  "ml-2 inline-flex h-5 items-center rounded-full border px-2 text-[10px] tabular-nums";

function queryMatches(occ: RhViolationOccurrence, q: string) {
  if (!q) return true;
  const v = occ.violation;
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

function pillClasses(active: boolean, color: "red" | "amber" | "sky") {
  if (color === "red") {
    return active
      ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
      : "border border-destructive/40 text-destructive hover:bg-destructive/10";
  }

  if (color === "amber") {
    return active
      ? "bg-amber-500 text-white hover:bg-amber-600"
      : "border border-amber-500/40 text-amber-700 hover:bg-amber-50";
  }

  // sky
  return active
    ? "bg-sky-500 text-white hover:bg-sky-600"
    : "border border-sky-500/40 text-sky-700 hover:bg-sky-50";
}

function buildInfoTooltip(counts: Counts) {
  return [
    `${counts.error} bloquant${counts.error > 1 ? "s" : ""}`,
    `${counts.warning} alerte${counts.warning > 1 ? "s" : ""}`,
    `${counts.info} info${counts.info > 1 ? "s" : ""}`,
  ].join(" · ");
}

function getAgentsFromGroup(items: RhViolationOccurrence[]): AgentBadge[] {
  const seen = new Map<number, string>();
  for (const occ of items) {
    if (occ.context.kind !== "agent") continue;
    if (!seen.has(occ.context.agent_id)) {
      seen.set(occ.context.agent_id, occ.context.label);
    }
  }
  return Array.from(seen.entries()).map(([id, label]) => ({ id, label }));
}

function calcDayCount(startISO: string | null, endISO: string | null) {
  if (!startISO || !endISO) return null;
  return (
    differenceInCalendarDays(new Date(endISO + "T00:00:00"), new Date(startISO + "T00:00:00")) + 1
  );
}

function buildRangeLabel(baseLabel: string, dayCount: number | null) {
  if (!dayCount || dayCount <= 1) return baseLabel;
  return `${baseLabel} · ${dayCount} jours`;
}

/* ------------------------------ Subcomponents ------------------------------ */

function AgentContextPill({ agents }: { agents: AgentBadge[] }) {
  const sorted = React.useMemo(() => {
    return agents.slice().sort((a, b) => a.label.localeCompare(b.label));
  }, [agents]);

  if (sorted.length === 0) return null;

  if (sorted.length === 1) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border bg-background px-2 py-0.5 text-[11px]">
        <User className="h-3.5 w-3.5" />
        <span className="truncate max-w-[220px]">{sorted[0].label}</span>
      </span>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex items-center gap-1 rounded-full border bg-background px-2 py-0.5 text-[11px] cursor-pointer">
          <Users className="h-3.5 w-3.5" />
          <span>{sorted.length} agents</span>
        </span>
      </TooltipTrigger>

      <TooltipContent side="bottom" align="start" className="max-w-xs p-3">
        <div className="mb-2 text-xs font-medium">Agents concernés</div>
        <div className="max-h-52 overflow-auto space-y-1">
          {sorted.map((a) => (
            <div key={a.id} className="text-xs">
              {a.label}
            </div>
          ))}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}

function NavButton({
  label,
  iso,
  icon,
  onJumpToDate,
  closeSheet,
}: {
  label: "Début" | "Fin";
  iso: string;
  icon: React.ReactNode;
  onJumpToDate: (isoDate: string) => void;
  closeSheet: () => void;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-8 px-2 gap-1"
          onClick={() => {
            onJumpToDate(iso);
            closeSheet();
          }}
        >
          {label === "Début" ? icon : null}
          {label}
          {label === "Fin" ? icon : null}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom" align="start">
        <p className="text-xs">Aller au {formatDateFRLong(iso)}</p>
      </TooltipContent>
    </Tooltip>
  );
}

function SheetHeader({
  startDate,
  endDate,
  counts,
  show,
  onToggle,
  query,
  onQueryChange,
  filteredCount,
  groupsCount,
  onReset,
}: {
  startDate: string;
  endDate: string;
  counts: Counts;
  show: Record<Severity, boolean>;
  onToggle: (sev: Severity) => void;
  query: string;
  onQueryChange: (v: string) => void;
  filteredCount: number;
  groupsCount: number;
  onReset: () => void;
}) {
  const infoTooltip = React.useMemo(() => buildInfoTooltip(counts), [counts]);

  return (
    <div className="space-y-3">
      {/* Row 1: période + compteur compact */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="text-sm text-muted-foreground">
          {formatDateFRLong(startDate)} → {formatDateFRLong(endDate)}
        </div>

        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex flex-wrap items-center gap-3 sm:justify-end cursor-default">
              {counts.error > 0 ? (
                <div className="flex items-center gap-1">
                  <OctagonAlert className="h-4 w-4 text-destructive" />
                  <span className="text-sm tabular-nums">{counts.error}</span>
                </div>
              ) : null}

              {counts.warning > 0 ? (
                <div className="flex items-center gap-1">
                  <TriangleAlert className="h-4 w-4 text-amber-600" />
                  <span className="text-sm tabular-nums">{counts.warning}</span>
                </div>
              ) : null}

              {counts.error === 0 && counts.warning === 0 ? (
                <div className="flex items-center gap-1">
                  <CheckCircle className="h-4 w-4 text-emerald-600" />
                  <span className="text-sm tabular-nums">OK</span>
                </div>
              ) : null}
            </div>
          </TooltipTrigger>

          <TooltipContent side="bottom" align="end">
            <p className="text-xs">
              {counts.error === 0 && counts.warning === 0
                ? "Aucun bloquant ni alerte."
                : infoTooltip}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="h-px bg-border" />

      {/* Row 2: filtres */}
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className={`h-9 rounded-full ${pillClasses(show.error, "red")}`}
          onClick={() => onToggle("error")}
        >
          Bloquants
          <span className={COUNT_PILL_CLASS}>{counts.error}</span>
        </Button>

        <Button
          type="button"
          size="sm"
          variant="ghost"
          className={`h-9 rounded-full ${pillClasses(show.warning, "amber")}`}
          onClick={() => onToggle("warning")}
        >
          Alertes
          <span className={COUNT_PILL_CLASS}>{counts.warning}</span>
        </Button>

        <Button
          type="button"
          size="sm"
          variant="ghost"
          className={`h-9 rounded-full ${pillClasses(show.info, "sky")}`}
          onClick={() => onToggle("info")}
        >
          Infos
          <span className={COUNT_PILL_CLASS}>{counts.info}</span>
        </Button>
      </div>

      {/* Row 3: search */}
      <div className="relative w-full sm:max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Rechercher (message, règle, code)…"
          className="h-10 pl-9"
        />
      </div>

      {/* Row 4: stats + reset */}
      <div className="pt-2 border-t border-border/50">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="h-6 rounded-full px-2 py-0 text-[11px] tabular-nums">
              {filteredCount} affichée(s)
            </Badge>
            <Badge variant="outline" className="h-6 rounded-full px-2 py-0 text-[11px] tabular-nums">
              {groupsCount} problème(s)
            </Badge>
          </div>

          <Button type="button" size="sm" variant="ghost" className="h-8" onClick={onReset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Réinitialiser
          </Button>
        </div>
      </div>
    </div>
  );
}

/* --------------------------------- Component -------------------------------- */

export function RhViolationsSheet({
  disabled = false,
  startDate,
  endDate,
  items,
  counts,
  loading = false,
  onJumpToDate,
}: {
  disabled?: boolean;
  startDate: string;
  endDate: string;
  items: RhViolationOccurrence[];
  counts: Counts;
  loading?: boolean;
  onJumpToDate?: (isoDate: string) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [show, setShow] = React.useState<Record<Severity, boolean>>(DEFAULT_SHOW);
  const [query, setQuery] = React.useState("");

  const toggle = React.useCallback((sev: Severity) => {
    setShow((s) => ({ ...s, [sev]: !s[sev] }));
  }, []);

  const reset = React.useCallback(() => {
    setShow(DEFAULT_SHOW);
    setQuery("");
  }, []);

  const closeSheet = React.useCallback(() => setOpen(false), []);

  const filtered = React.useMemo(() => {
    return (items ?? [])
      .filter((occ) => show[(occ.violation.severity as Severity) ?? "info"])
      .filter((occ) => queryMatches(occ, query));
  }, [items, show, query]);

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
          <SheetHeader
            startDate={startDate}
            endDate={endDate}
            counts={counts}
            show={show}
            onToggle={toggle}
            query={query}
            onQueryChange={setQuery}
            filteredCount={filtered.length}
            groupsCount={groups.length}
            onReset={reset}
          />
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

                const dayCount = calcDayCount(startISO, endISO);
                const rangeLabel = buildRangeLabel(g.range.label, dayCount);

                const title = (g.rule && g.rule.trim().length > 0 ? g.rule : g.code) ?? "Violation";

                const agents = getAgentsFromGroup(g.items);
                const contextSlot = agents.length > 0 ? <AgentContextPill agents={agents} /> : null;

                const actionsSlot =
                  onJumpToDate && (startISO || (endISO && endISO !== startISO)) ? (
                    <>
                      {startISO ? (
                        <NavButton
                          label="Début"
                          iso={startISO}
                          icon={<ArrowLeft className="h-4 w-4" />}
                          onJumpToDate={onJumpToDate}
                          closeSheet={closeSheet}
                        />
                      ) : null}

                      {endISO && endISO !== startISO ? (
                        <NavButton
                          label="Fin"
                          iso={endISO}
                          icon={<ArrowRight className="h-4 w-4" />}
                          onJumpToDate={onJumpToDate}
                          closeSheet={closeSheet}
                        />
                      ) : null}
                    </>
                  ) : null;

                return (
                  <div key={g.key}>
                    <RhViolationCard
                      severity={g.severity}
                      title={title}
                      message={g.message}
                      rangeLabel={rangeLabel}
                      count={g.count}
                      contextSlot={contextSlot}
                      actionsSlot={actionsSlot}
                    />
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
