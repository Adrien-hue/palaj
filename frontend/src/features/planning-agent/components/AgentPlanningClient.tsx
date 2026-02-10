"use client";

import * as React from "react";
import { startOfMonth, endOfMonth, set } from "date-fns";

import { buildPlanningVm } from "@/features/planning-agent/vm/agentPlanning.vm.builder";
import { useAgentPlanning } from "@/features/planning-agent/hooks/useAgentPlanning";

import { PlanningPageHeader } from "@/features/planning-common/components/PlanningPageHeader";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";

import { AgentHeaderSelect } from "@/features/planning-agent/components/AgentHeaderSelect";
import { AgentPlanningGrid } from "@/features/planning-agent/components/AgentPlanningGrid";
import { AgentDaySheet } from "@/features/planning-agent/components/AgentDaySheet";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { formatDateFR, toISODate } from "@/utils/date.format";

import type { AgentPlanningKey } from "@/features/planning-agent/hooks/agentPlanning.key";
import { AgentBulkEditSheet } from "./AgentBulkEditSheet";

type AgentListItem = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string | null;
  actif: boolean;
};

export function AgentPlanningClient({
  initialAgentId = null,
  initialAnchor,
  agents,
}: {
  initialAgentId?: number | null;
  initialAnchor: string;
  agents: AgentListItem[];
}) {
  const [agentId, setAgentId] = React.useState<number | null>(initialAgentId);

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

  const subtitle = React.useMemo(() => {
    return range.isRange
      ? `Planning du ${formatDateFR(range.start)} au ${formatDateFR(range.end)}`
      : "Planning mensuel";
  }, [range.start, range.end, range.isRange]);

  const { data, error, isLoading, isValidating } = useAgentPlanning({
    agentId,
    startDate: range.start,
    endDate: range.end,
  });

  const planningVm = React.useMemo(() => {
    if (!data) return null;
    return buildPlanningVm(data);
  }, [data]);

  const planningKey = React.useMemo<AgentPlanningKey | null>(() => {
    if (agentId === null) return null;
    return ["agentPlanning", agentId, range.start, range.end] as const;
  }, [agentId, range.start, range.end]);

  const [selectedDayDate, setSelectedDayDate] = React.useState<string | null>(
    null,
  );
  const [sheetOpen, setSheetOpen] = React.useState(false);

  const [multiSelect, setMultiSelect] = React.useState(false);

  const toggleMultiSelect = React.useCallback(() => {
    setMultiSelect((v) => {
      const next = !v;
      if (next) {
        clearMultiSelection();
      }
      return next;
    });
  }, []);

  const [selectedDates, setSelectedDates] = React.useState<Set<string>>(
    () => new Set(),
  );
  const [anchorDate, setAnchorDate] = React.useState<string | null>(null);

  const selectedCount = selectedDates.size;

  const clearMultiSelection = React.useCallback(() => {
    setSelectedDates(new Set());
    setAnchorDate(null);
  }, []);

  const exitMultiSelect = React.useCallback(() => {
    setMultiSelect(false);
    clearMultiSelection();
  }, [clearMultiSelection]);

  const selectedDay = React.useMemo(() => {
    if (!planningVm || !selectedDayDate) return null;
    return planningVm.days.find((d) => d.day_date === selectedDayDate) ?? null;
  }, [planningVm, selectedDayDate]);

  const handleMultiSelectDay = React.useCallback(
    (iso: string, e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();

      setSelectedDates((prev) => {
        const next = new Set(prev);

        if (e.shiftKey && anchorDate && planningVm) {
          const ordered = planningVm.days
            .map((d) => d.day_date)
            .slice()
            .sort((a, b) => a.localeCompare(b));

          const a = ordered.indexOf(anchorDate);
          const b = ordered.indexOf(iso);

          if (a !== -1 && b !== -1) {
            const [start, end] = a < b ? [a, b] : [b, a];
            for (let i = start; i <= end; i++) next.add(ordered[i]);
            return next;
          }
        }

        if (next.has(iso)) next.delete(iso);
        else next.add(iso);

        return next;
      });

      setAnchorDate((prev) => (e.shiftKey ? (prev ?? iso) : iso));
    },
    [anchorDate, planningVm],
  );

  React.useEffect(() => {
    setSheetOpen(false);
    setSelectedDayDate(null);
    setMultiSelect(false);
    clearMultiSelection();
  }, [agentId, range.start, range.end, clearMultiSelection]);

  React.useEffect(() => {
    if (sheetOpen && selectedDayDate && planningVm) {
      const stillExists = planningVm.days.some(
        (d) => d.day_date === selectedDayDate,
      );
      if (!stillExists) {
        setSheetOpen(false);
        setSelectedDayDate(null);
      }
    }
  }, [sheetOpen, selectedDayDate, planningVm]);

  const headerSubtitle =
    agentId === null
      ? subtitle
      : isLoading
        ? "Chargement…"
        : error
          ? "Erreur de chargement du planning"
          : isValidating
            ? "Mise à jour…"
            : subtitle;

  const anchorMonth = React.useMemo(() => {
    if (period.kind === "month") return toISODate(startOfMonth(period.month));
    return toISODate(startOfMonth(new Date(range.start + "T00:00:00")));
  }, [period, range.start]);

  const [bulkOpen, setBulkOpen] = React.useState(false);

  const selectedDatesSorted = React.useMemo(
    () => Array.from(selectedDates).sort((a, b) => a.localeCompare(b)),
    [selectedDates],
  );

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        titleSlot={
          <AgentHeaderSelect
            agents={agents}
            valueId={agentId}
            onChange={(id) => setAgentId(id)}
          />
        }
        subtitle={headerSubtitle}
        rightSlot={
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2 cursor-pointer">
                    <Switch
                      id="multi-select"
                      checked={multiSelect}
                      onCheckedChange={toggleMultiSelect}
                    />
                    <Label htmlFor="multi-select">Sélection multiple</Label>
                  </div>
                </TooltipTrigger>

                <TooltipContent side="bottom" align="start">
                  <p className="text-sm">
                    Sélectionnez plusieurs jours pour leur appliquer un statut,
                    <br />
                    une tranche et un commentaire en une seule fois.
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>

            <PlanningPeriodControls
              value={period}
              onChange={setPeriod}
              onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
              onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
              disabled={agentId !== null && isLoading}
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
                    ? "jours sélectionnés"
                    : "jour sélectionné"}
                </span>
                {selectedCount === 0 ? (
                  <span className="text-muted-foreground">
                    — cliquez pour sélectionner, Shift pour une plage
                  </span>
                ) : null}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={clearMultiSelection}
                  disabled={selectedCount === 0}
                >
                  Tout désélectionner
                </Button>

                <Button
                  type="button"
                  onClick={() => setBulkOpen(true)}
                  disabled={selectedCount === 0}
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

      {agentId === null ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Veuillez sélectionner un agent pour afficher son planning.
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Impossible de charger le planning. {(error as Error).message}
          </CardContent>
        </Card>
      ) : planningVm ? (
        range.isRange ? (
          <AgentPlanningGrid
            mode="range"
            startDate={range.start}
            endDate={range.end}
            planning={planningVm}
            multiSelect={multiSelect}
            multiSelectedDates={selectedDates}
            onMultiSelectDay={(day, e) => handleMultiSelectDay(day.day_date, e)}
            onDayClick={(day) => {
              if (multiSelect) return;
              setSelectedDayDate(day.day_date);
              setSheetOpen(true);
            }}
          />
        ) : (
          <AgentPlanningGrid
            mode="month"
            anchorMonth={anchorMonth}
            planning={planningVm}
            multiSelect={multiSelect}
            multiSelectedDates={selectedDates}
            onMultiSelectDay={(day, e) => handleMultiSelectDay(day.day_date, e)}
            onDayClick={(day) => {
              if (multiSelect) return;
              setSelectedDayDate(day.day_date);
              setSheetOpen(true);
            }}
          />
        )
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Chargement du planning…
          </CardContent>
        </Card>
      )}

      {agentId !== null ? (
        <AgentDaySheet
          open={sheetOpen}
          onClose={() => setSheetOpen(false)}
          dayDateISO={selectedDayDate}
          agentId={agentId}
          planningKey={planningKey}
        />
      ) : null}

      {agentId !== null ? (
        <AgentBulkEditSheet
          open={bulkOpen}
          onClose={() => setBulkOpen(false)}
          agentId={agentId}
          planningKey={planningKey}
          selectedDates={selectedDatesSorted}
          onApplied={() => {
            // après succès: on clear la sélection et on reste en mode multi (ou pas)
            clearMultiSelection();
            // option: setMultiSelect(false);
          }}
        />
      ) : null}
    </div>
  );
}
