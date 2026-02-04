"use client";

import * as React from "react";
import { startOfMonth, endOfMonth } from "date-fns";

import { buildPlanningVm } from "@/features/planning-agent/vm/agentPlanning.vm.builder";
import { useAgentPlanning } from "@/features/planning-agent/hooks/useAgentPlanning";

import { PlanningPageHeader } from "@/features/planning-common/components/PlanningPageHeader";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";

import { AgentHeaderSelect } from "@/features/planning-agent/components/AgentHeaderSelect";
import { AgentPlanningGrid } from "@/features/planning-agent/components/AgentPlanningGrid";
import { AgentDaySheet } from "@/features/planning-agent/components/AgentDaySheet";

import { Card, CardContent } from "@/components/ui/card";
import { formatDateFR, toISODate } from "@/utils/date.format";

import type { AgentDayVm } from "@/features/planning-agent/vm/agentPlanning.vm";
import type { AgentPlanningKey } from "@/features/planning-agent/hooks/agentPlanning.key";

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
  postes,
}: {
  initialAgentId?: number | null;
  initialAnchor: string;
  agents: AgentListItem[];
  postes: { id: number; nom: string }[];
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

  const posteNameById = React.useMemo(
    () => new Map<number, string>(postes.map((p) => [p.id, p.nom])),
    [postes],
  );

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

  const selectedDay = React.useMemo(() => {
    if (!planningVm || !selectedDayDate) return null;
    return planningVm.days.find((d) => d.day_date === selectedDayDate) ?? null;
  }, [planningVm, selectedDayDate]);

  React.useEffect(() => {
    setSheetOpen(false);
    setSelectedDayDate(null);
  }, [agentId, range.start, range.end]);

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
          <PlanningPeriodControls
            value={period}
            onChange={setPeriod}
            onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
            onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
            disabled={agentId !== null && isLoading}
          />
        }
      />

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
            onDayClick={(day) => {
              setSelectedDayDate(day.day_date);
              setSheetOpen(true);
            }}
          />
        ) : (
          <AgentPlanningGrid
            mode="month"
            anchorMonth={anchorMonth}
            planning={planningVm}
            onDayClick={(day) => {
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
          selectedDay={selectedDay}
          posteNameById={posteNameById}
          agentId={agentId}
          planningKey={planningKey}
        />
      ) : null}
    </div>
  );
}
