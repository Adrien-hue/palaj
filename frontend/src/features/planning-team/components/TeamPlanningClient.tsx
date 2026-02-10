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

import { Card, CardContent } from "@/components/ui/card";
import { formatDateFR, toISODate } from "@/utils/date.format";

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

  const planningVm = React.useMemo(() => {
    if (!data) return null;
    return buildTeamPlanningVm(data);
  }, [data]);

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

  // Sheet state
  const [sheetOpen, setSheetOpen] = React.useState(false);
  const [selectedAgentId, setSelectedAgentId] = React.useState<number | null>(null);
  const [selectedDayDateISO, setSelectedDayDateISO] = React.useState<string | null>(null);

  const openSheet = React.useCallback((agent: Agent, day: AgentDay) => {
    setSelectedAgentId(agent.id);
    setSelectedDayDateISO(day.day_date);
    setSheetOpen(true);
  }, []);

  React.useEffect(() => {
    setSheetOpen(false);
    setSelectedAgentId(null);
    setSelectedDayDateISO(null);
  }, [teamId, range.start, range.end]);

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
          <PlanningPeriodControls
            value={period}
            onChange={setPeriod}
            onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
            onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
            disabled={teamId !== null && isLoading}
          />
        }
      />

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
          onCellClick={openSheet}
        />
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Aucun jour à afficher pour cette période.
          </CardContent>
        </Card>
      )}

      {/* Sheet */}
      <AgentDaySheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        agentId={selectedAgentId ?? 0}
        dayDateISO={selectedDayDateISO}
        onChanged={async () => {
          await mutate();
        }}
      />
    </div>
  );
}
