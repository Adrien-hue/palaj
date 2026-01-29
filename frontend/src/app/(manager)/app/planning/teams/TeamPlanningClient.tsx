"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { listTeams } from "@/services/teams.service";
import { getTeamPlanning } from "@/services/planning.service";
import type { Team, TeamPlanning, AgentDay, Agent } from "@/types";
import { TeamDaySheet } from "@/features/planning-team/TeamDaySheet";
import {
  addDays,
  formatDayLabel,
  parseISODate,
  startOfWeekMonday,
  toISODate,
} from "@/utils/date.format";

import { TeamPlanningHeader } from "@/features/planning-team/TeamPlanningHeader";
import { TeamPlanningMatrix } from "@/features/planning-team/TeamPlanningMatrix";
import { CellSegment } from "@/features/planning-team/DayCell";

function getParamInt(sp: URLSearchParams, key: string): number | null {
  const v = sp.get(key);
  if (!v) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export default function TeamPlanningClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [teams, setTeams] = React.useState<Team[]>([]);
  const [loadingTeams, setLoadingTeams] = React.useState(true);

  const [planning, setPlanning] = React.useState<TeamPlanning | null>(null);
  const [loadingPlanning, setLoadingPlanning] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [selectedSegments, setSelectedSegments] = React.useState<CellSegment[]>([]);

  // Sheet state
  const [sheetOpen, setSheetOpen] = React.useState(false);
  const [selectedAgent, setSelectedAgent] = React.useState<Agent | null>(null);
  const [selectedDay, setSelectedDay] = React.useState<AgentDay | null>(null);

  const teamId = getParamInt(
    searchParams as unknown as URLSearchParams,
    "teamId"
  ); // next types
  const startParam = (searchParams as unknown as URLSearchParams).get("start");

  const startDate = React.useMemo(() => {
    const parsed = startParam ? parseISODate(startParam) : null;
    if (parsed) return parsed;
    return startOfWeekMonday(new Date());
  }, [startParam]);

  const startISO = React.useMemo(() => toISODate(startDate), [startDate]);
  const endISO = React.useMemo(
    () => toISODate(addDays(startDate, 27)),
    [startDate]
  );

  // Load teams once
  React.useEffect(() => {
    let cancelled = false;
    setLoadingTeams(true);
    setError(null);

    listTeams({ page: 1, page_size: 200 })
      .then((res) => {
        if (cancelled) return;
        setTeams(res.items ?? []);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(
          e instanceof Error
            ? e.message
            : "Erreur lors du chargement des équipes"
        );
      })
      .finally(() => {
        if (cancelled) return;
        setLoadingTeams(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // Ensure defaults in URL once teams are loaded
  React.useEffect(() => {
    if (loadingTeams) return;
    if (!teams.length) return;

    const sp = new URLSearchParams(
      (searchParams as unknown as URLSearchParams).toString()
    );
    let changed = false;

    if (!teamId) {
      sp.set("teamId", String(teams[0].id));
      changed = true;
    }
    if (!startParam) {
      sp.set("start", startISO);
      changed = true;
    }

    if (changed) {
      router.replace(`?${sp.toString()}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadingTeams, teams, teamId, startParam, startISO]);

  // Load planning when params ready
  React.useEffect(() => {
    if (!teamId) return;
    if (!startISO) return;

    let cancelled = false;
    setLoadingPlanning(true);
    setError(null);

    getTeamPlanning(teamId, { startDate: startISO, endDate: endISO })
      .then((res) => {
        if (cancelled) return;
        setPlanning(res);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setPlanning(null);
        setError(
          e instanceof Error
            ? e.message
            : "Erreur lors du chargement du planning"
        );
      })
      .finally(() => {
        if (cancelled) return;
        setLoadingPlanning(false);
      });

    return () => {
      cancelled = true;
    };
  }, [teamId, startISO, endISO]);

  const onChangeTeam = (newTeamId: number) => {
    const sp = new URLSearchParams(
      (searchParams as unknown as URLSearchParams).toString()
    );
    sp.set("teamId", String(newTeamId));
    // on garde start
    if (!sp.get("start")) sp.set("start", startISO);
    router.push(`?${sp.toString()}`);
  };

  const goToday = () => {
    const monday = startOfWeekMonday(new Date());
    const sp = new URLSearchParams(searchParams.toString());
    sp.set("start", toISODate(monday));
    if (!sp.get("teamId") && teams[0]) sp.set("teamId", String(teams[0].id));
    router.push(`?${sp.toString()}`);
  };

  const shiftWeek = (deltaWeeks: number) => {
    const nextStart = addDays(startDate, deltaWeeks * 7);
    const sp = new URLSearchParams(searchParams.toString());
    sp.set("start", toISODate(nextStart));
    router.push(`?${sp.toString()}`);
  };

  const openSheet = (agent: Agent, day: AgentDay, segments: CellSegment[]) => {
    setSelectedAgent(agent);
    setSelectedDay(day);
    setSelectedSegments(segments);
    setSheetOpen(true);
  };

  const days = planning?.days ?? [];

  return (
    <div className="flex flex-col gap-4">
      {/* Page header */}
      <TeamPlanningHeader
        teams={teams}
        teamId={teamId}
        teamName={planning?.team.name}
        agentsCount={planning?.agents.length}
        startISO={startISO}
        endISO={endISO}
        loadingTeams={loadingTeams}
        loadingPlanning={loadingPlanning}
        error={error}
        onChangeTeam={onChangeTeam}
        onGoToday={goToday}
        onShiftWeek={shiftWeek}
      />

      <TeamPlanningMatrix
        days={days}
        rows={planning?.agents ?? []}
        loading={loadingPlanning}
        formatDayLabel={formatDayLabel}
        onCellClick={(agent, day, selectedSegments) => openSheet(agent, day, selectedSegments)}
      />

      <TeamDaySheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        agent={selectedAgent}
        day={selectedDay}
        segments={selectedSegments}
      />
    </div>
  );
}
