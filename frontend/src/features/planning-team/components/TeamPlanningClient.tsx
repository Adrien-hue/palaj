"use client";

import * as React from "react";
import { startOfMonth, endOfMonth } from "date-fns";

import type { Agent, AgentDay, Team } from "@/types";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";

import { useTeamPlanning } from "@/features/planning-team/hooks/useTeamPlanning";
import { buildTeamPlanningVm } from "@/features/planning-team/vm/teamPlanning.vm.builder";

import { PlanningPageHeader } from "@/features/planning-common/components/PlanningPageHeader";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";

import { TeamHeaderSelect } from "@/features/planning-team/components/TeamHeaderSelect";
import { TeamPlanningMatrix } from "@/features/planning-team/components/TeamPlanningMatrix";
import { AgentDaySheet } from "@/features/planning-agent/components/AgentDaySheet";

import { RhViolationsSheet } from "@/features/rh-validation/components/RhViolationsSheet";
import { useRhValidationTeam } from "@/features/rh-validation/hooks/useRhValidationTeam";

import { Card, CardContent } from "@/components/ui/card";
import { formatDateFR, toISODate } from "@/utils/date.format";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { TeamBulkEditSheet } from "./TeamBulkEditSheet";
import type { TeamPlanningBulkItem } from "@/types/teamPlanning";

type CellKey = `${number}__${string}`;
const cellKey = (agentId: number, dayDateISO: string) =>
  `${agentId}__${dayDateISO}` as CellKey;

function parseCellKey(key: CellKey): { agentId: number; dayDateISO: string } {
  const [a, d] = key.split("__");
  return { agentId: Number(a), dayDateISO: d };
}

export function TeamPlanningClient({
  initialTeamId = null,
  initialAnchor, // YYYY-MM-01 (ou YYYY-MM-DD, on normalise)
  teams,
}: {
  initialTeamId?: number | null;
  initialAnchor: string;
  teams: Team[];
}) {
  const [teamId, setTeamId] = React.useState<number | null>(initialTeamId);

  // Period state (month/range)
  const [period, setPeriod] = React.useState<PlanningPeriod>(() => {
    const base = startOfMonth(new Date(initialAnchor + "T00:00:00"));
    return { kind: "month", month: base };
  });

  const range = React.useMemo(() => {
    if (period.kind === "month") {
      const start = startOfMonth(period.month);
      const end = endOfMonth(period.month);
      return { start: toISODate(start), end: toISODate(end), isRange: false };
    }

    return {
      start: toISODate(period.start),
      end: toISODate(period.end),
      isRange: true,
    };
  }, [period]);

  const startDate = range.start;
  const endDate = range.end;

  const subtitle = React.useMemo(() => {
    return range.isRange
      ? `Planning du ${formatDateFR(range.start)} au ${formatDateFR(range.end)}`
      : "Planning mensuel";
  }, [range.start, range.end, range.isRange]);

  // Data
  const { data, error, isLoading, isValidating, mutate } = useTeamPlanning({
    teamId,
    startDate: range.start,
    endDate: range.end,
  });

  const rh = useRhValidationTeam({
    teamId,
    startDate,
    endDate,
    profile: "full", // ou state si tu veux un toggle plus tard
    enabled: teamId !== null,
  });

  const planningVm = React.useMemo(() => {
    if (!data) return null;
    return buildTeamPlanningVm(data);
  }, [data]);

  const agentLabelById = React.useMemo(() => {
    const map = new Map<number, string>();
    for (const row of planningVm?.rows ?? []) {
      const a = row.agent;
      map.set(
        a.id,
        `${a.prenom} ${a.nom}`,
      );
    }
    return map;
  }, [planningVm]);

  const rhItems = React.useMemo(() => {
    const results = rh.data?.results ?? [];
    return results.flatMap((r) => {
      const label = agentLabelById.get(r.agent_id) ?? `Agent #${r.agent_id}`;
      return (r.result.violations ?? []).map((v) => ({
        violation: v,
        context: { kind: "agent" as const, agent_id: r.agent_id, label },
      }));
    });
  }, [rh.data, agentLabelById]);

  const rhCounts = React.useMemo(() => {
    let info = 0,
      warning = 0,
      error = 0;
    for (const it of rhItems) {
      if (it.violation.severity === "info") info++;
      else if (it.violation.severity === "warning") warning++;
      else if (it.violation.severity === "error") error++;
    }
    return { info, warning, error, total: info + warning + error };
  }, [rhItems]);

  const headerSubtitle =
    teamId === null
      ? subtitle
      : isLoading
        ? "Chargement…"
        : error
          ? "Erreur de chargement du planning"
          : isValidating
            ? "Mise à jour…"
            : subtitle;

  // -----
  // Sheet state (single edit)
  // -----
  const [sheetOpen, setSheetOpen] = React.useState(false);
  const [selectedAgentId, setSelectedAgentId] = React.useState<number | null>(
    null,
  );
  const [selectedDayDateISO, setSelectedDayDateISO] = React.useState<
    string | null
  >(null);

  // -----
  // Multi-select state
  // -----
  const [multiSelect, setMultiSelect] = React.useState(false);
  const [selectedKeys, setSelectedKeys] = React.useState<Set<CellKey>>(
    () => new Set(),
  );
  const [anchorKey, setAnchorKey] = React.useState<CellKey | null>(null);

  const selectedCount = selectedKeys.size;

  const clearSelection = React.useCallback(() => {
    setSelectedKeys(new Set());
    setAnchorKey(null);
  }, []);

  const exitMultiSelect = React.useCallback(() => {
    setBulkOpen(false);
    setMultiSelect(false);
    clearSelection();
  }, [clearSelection]);

  const toggleMultiSelect = React.useCallback(() => {
    setMultiSelect((v) => {
      const next = !v;
      if (next) {
        // entering multi: close single sheet and reset selection
        setSheetOpen(false);
        setSelectedAgentId(null);
        setSelectedDayDateISO(null);
        clearSelection();
      }
      return next;
    });
  }, [clearSelection]);

  // Reset on team/period change
  React.useEffect(() => {
    setSheetOpen(false);
    setSelectedAgentId(null);
    setSelectedDayDateISO(null);
    setMultiSelect(false);
    clearSelection();
  }, [teamId, range.start, range.end, clearSelection]);

  // Ordered days for shift-range
  const orderedDays = React.useMemo(() => {
    return (planningVm?.days ?? []).slice().sort((a, b) => a.localeCompare(b));
  }, [planningVm?.days]);

  // Main click handler for matrix cells
  const handleCellClick = React.useCallback(
    (agent: Agent, day: AgentDay, e: React.MouseEvent) => {
      if (!multiSelect) {
        setSelectedAgentId(agent.id);
        setSelectedDayDateISO(day.day_date);
        setSheetOpen(true);
        return;
      }

      e.preventDefault();

      const key = cellKey(agent.id, day.day_date);

      setSelectedKeys((prev) => {
        const next = new Set(prev);

        // SHIFT range selection: only within same agent row
        if (e.shiftKey && anchorKey) {
          const a = parseCellKey(anchorKey);

          if (a.agentId === agent.id) {
            const startIdx = orderedDays.indexOf(a.dayDateISO);
            const endIdx = orderedDays.indexOf(day.day_date);

            if (startIdx !== -1 && endIdx !== -1) {
              const [s, t] =
                startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];

              for (let i = s; i <= t; i++) {
                next.add(cellKey(agent.id, orderedDays[i]));
              }
              return next;
            }
          }
        }

        // Toggle current cell
        if (next.has(key)) next.delete(key);
        else next.add(key);

        return next;
      });

      setAnchorKey((prev) => (e.shiftKey ? (prev ?? key) : key));
    },
    [multiSelect, anchorKey, orderedDays],
  );

  // -----
  // Bulk sheet
  // -----
  const [bulkOpen, setBulkOpen] = React.useState(false);

  const bulkItems: TeamPlanningBulkItem[] = React.useMemo(() => {
    const map = new Map<number, Set<string>>();

    for (const k of selectedKeys) {
      const { agentId, dayDateISO } = parseCellKey(k);
      if (!map.has(agentId)) map.set(agentId, new Set());
      map.get(agentId)!.add(dayDateISO);
    }

    return Array.from(map.entries())
      .sort(([a], [b]) => a - b)
      .map(([agent_id, dates]) => ({
        agent_id,
        day_dates: Array.from(dates).sort((a, b) => a.localeCompare(b)),
      }));
  }, [selectedKeys]);

  const canOpenBulk = bulkItems.length > 0;

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        titleSlot={
          <TeamHeaderSelect
            teams={teams}
            valueId={teamId}
            onChange={(id) => setTeamId(id)}
          />
        }
        subtitle={headerSubtitle}
        rightSlot={
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2 cursor-pointer">
                    <Switch
                      id="multi-select"
                      checked={multiSelect}
                      onCheckedChange={toggleMultiSelect}
                      disabled={teamId !== null && isLoading}
                    />
                    <Label htmlFor="multi-select">Sélection multiple</Label>
                  </div>
                </TooltipTrigger>

                <TooltipContent side="bottom" align="start">
                  <p className="text-sm">
                    Sélectionnez plusieurs cellules pour appliquer un statut,
                    <br />
                    une tranche et un commentaire en une seule fois.
                    <br />
                    <span className="text-muted-foreground">
                      Astuce : Shift pour une plage (même agent).
                    </span>
                  </p>
                </TooltipContent>
              </Tooltip>

              <PlanningPeriodControls
                value={period}
                onChange={setPeriod}
                onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
                onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
                disabled={teamId !== null && isLoading}
              />
            </div>

            <RhViolationsSheet
              disabled={teamId === null}
              startDate={startDate}
              endDate={endDate}
              items={rhItems}
              counts={rhCounts}
              loading={rh.isLoading || rh.isValidating}
            />
          </div>
        }
      />

      {multiSelect ? (
        <div className="sticky top-0 z-10">
          <div className="rounded-xl border bg-card/95 p-3 shadow-sm backdrop-blur">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">
                  {selectedCount}{" "}
                  {selectedCount > 1
                    ? "cellules sélectionnées"
                    : "cellule sélectionnée"}
                </span>
                {selectedCount === 0 ? (
                  <span className="text-muted-foreground">
                    — cliquez pour sélectionner, Shift pour une plage (même
                    agent)
                  </span>
                ) : null}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={clearSelection}
                  disabled={selectedCount === 0}
                >
                  Tout désélectionner
                </Button>

                <Button
                  type="button"
                  onClick={() => setBulkOpen(true)}
                  disabled={!canOpenBulk}
                >
                  Éditer
                </Button>

                <Button type="button" variant="ghost" onClick={exitMultiSelect}>
                  Quitter
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {teamId === null ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Veuillez sélectionner une équipe pour afficher son planning.
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Impossible de charger le planning. {(error as Error).message}
          </CardContent>
        </Card>
      ) : isLoading && !data ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Chargement du planning…
          </CardContent>
        </Card>
      ) : planningVm && planningVm.days.length > 0 ? (
        <TeamPlanningMatrix
          days={planningVm.days}
          rows={planningVm.rows}
          onCellClick={handleCellClick}
          selectedKeys={selectedKeys}
        />
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Aucun jour à afficher pour cette période.
          </CardContent>
        </Card>
      )}

      {/* Sheet (single edit) */}
      <AgentDaySheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        agentId={selectedAgentId ?? 0}
        dayDateISO={selectedDayDateISO}
        onChanged={async () => {
          await mutate();
        }}
      />

      {/* Sheet (bulk edit) */}
      {teamId !== null ? (
        <TeamBulkEditSheet
          open={bulkOpen}
          onClose={() => setBulkOpen(false)}
          teamId={teamId}
          items={bulkItems}
          onApplied={async () => {
            clearSelection();
            await mutate();
          }}
        />
      ) : null}
    </div>
  );
}
