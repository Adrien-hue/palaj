"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";

import { TeamSelect } from "./TeamSelect";
import type { Team } from "@/types/team";

type Props = {
  teams: Team[];
  teamId: number | null;

  teamName?: string;
  agentsCount?: number;

  startISO: string;
  endISO: string;

  loadingTeams?: boolean;
  loadingPlanning?: boolean;
  error?: string | null;

  onChangeTeam: (teamId: number) => void;
  onShiftWeek: (deltaWeeks: number) => void;
  onGoToday: () => void;
};

export function TeamPlanningHeader({
  teams,
  teamId,
  teamName,
  agentsCount,
  startISO,
  endISO,
  loadingTeams,
  loadingPlanning,
  error,
  onChangeTeam,
  onShiftWeek,
  onGoToday,
}: Props) {
  return (
    <div className="flex flex-col gap-4">
      {/* Title row */}
      <div className="flex flex-wrap items-end justify-between gap-3 px-1">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Planning par équipe</h1>
        </div>

        {/* Right side summary */}
        <div className="flex items-center gap-2">
          {teamName ? (
            <Badge variant="secondary" className="rounded-full">
              {teamName}
            </Badge>
          ) : null}
          {typeof agentsCount === "number" ? (
            <Badge variant="outline" className="rounded-full tabular-nums">
              {agentsCount} agent(s)
            </Badge>
          ) : null}
        </div>
      </div>

      {/* Toolbar */}
      <div className="sticky top-0 z-30">
        <Card className="relative overflow-hidden border bg-card shadow-md dark:shadow-black/40">
          {/* Accent bar */}
          <div className="absolute inset-y-0 left-0 w-2 bg-primary/60" />

          <CardContent className="bg-gradient-to-b from-card/95 to-card pl-5 pr-4 py-4">
            <div className="flex flex-wrap items-center gap-3">
              {/* Team select */}
              <TeamSelect teams={teams} value={teamId} onChange={onChangeTeam} disabled={loadingTeams} />

              {/* Nav group */}
              <div className="flex flex-wrap items-center gap-3">
                {/* Segmented controls */}
                <div className="inline-flex items-center">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => onShiftWeek(-1)}
                    disabled={!teamId}
                    className="h-9 w-9 rounded-r-none border-r-0"
                    aria-label="Semaine précédente"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    onClick={onGoToday}
                    disabled={!teamId}
                    className="h-9 rounded-none px-3"
                  >
                    Cette semaine
                  </Button>

                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => onShiftWeek(1)}
                    disabled={!teamId}
                    className="h-9 w-9 rounded-l-none border-l-0"
                    aria-label="Semaine suivante"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>

                {/* Range info (desktop) */}
                <div className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground">
                  <CalendarDays className="h-4 w-4" />
                  <span className="tabular-nums">
                    Fenêtre (4 semaines) : {startISO}
                    <span className="mx-1 text-muted-foreground/60">→</span>
                    {endISO}
                  </span>
                </div>
              </div>

              {/* Status */}
              <div className="ml-auto flex items-center gap-3">
                {/* Range info (mobile) */}
                <div className="sm:hidden flex items-center gap-2 text-sm text-muted-foreground">
                  <CalendarDays className="h-4 w-4" />
                  <span className="tabular-nums">
                    {startISO}
                    <span className="mx-1 text-muted-foreground/60">→</span>
                    {endISO}
                  </span>
                </div>

                {error ? (
                  <div className="text-sm text-destructive">{error}</div>
                ) : loadingPlanning ? (
                  <div className="text-sm text-muted-foreground">Chargement…</div>
                ) : null}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
