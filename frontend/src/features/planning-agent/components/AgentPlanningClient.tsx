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
import { AgentMonthlyPlanningGrid } from "@/features/planning-agent/components/AgentMonthlyPlanningGrid";

import { Card, CardContent } from "@/components/ui/card";
import { formatDateFR, toISODate } from "@/utils/date.format";

type AgentListItem = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string | null;
  actif: boolean;
};

export function AgentPlanningClient({
  initialAgentId = null,
  initialAnchor, // YYYY-MM-01 (ou YYYY-MM-DD, on normalise)
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
    [postes]
  );

  const planningVm = React.useMemo(() => {
    if (!data) return null;
    return buildPlanningVm(data);
  }, [data]);

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
        <AgentMonthlyPlanningGrid
          anchorMonth={toISODate(startOfMonth(new Date(range.start + "T00:00:00")))}
          planning={planningVm}
          posteNameById={posteNameById}
        />
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Chargement du planning…
          </CardContent>
        </Card>
      )}
    </div>
  );
}
