"use client";

import * as React from "react";
import type { Agent, AgentDay, TeamAgentPlanning } from "@/types";
import { cn } from "@/lib/utils";
import { TeamDayCell } from "./TeamDayCell";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { formatDayLabel, isWeekend } from "@/utils/date.format";

type Props = {
  days: string[];
  rows: TeamAgentPlanning[];
  emptyLabel?: string;

  onCellClick: (agent: Agent, day: AgentDay) => void;

  selected?: { agentId: number; dayDate: string } | null;
};

const AGENT_COL_W = 260;
const DAY_COL_W = 80;

function isMonday(isoDate: string) {
  return new Date(isoDate + "T00:00:00").getDay() === 1;
}

function todayISO(): string {
  const d = new Date();
  const yyyy = String(d.getFullYear());
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function TeamPlanningMatrix({
  days,
  rows,
  emptyLabel = "Aucun agent dans cette équipe.",
  onCellClick,
  selected = null,
}: Props) {
  if (days.length === 0) return null;

  const gridCols = React.useMemo(
    () => `${AGENT_COL_W}px repeat(${days.length}, ${DAY_COL_W}px)`,
    [days.length],
  );

  const today = React.useMemo(() => todayISO(), []);

  const colFlags = React.useMemo(
    () =>
      days.map((d) => ({
        weekStart: isMonday(d),
        weekend: isWeekend(d),
        today: d === today,
      })),
    [days, today],
  );

  return (
    <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
      <div className="overflow-auto">
        <div className="min-w-max">
          {/* Header row */}
          <div className="grid" style={{ gridTemplateColumns: gridCols }}>
            {/* Sticky corner */}
            <div
              className={cn(
                "sticky left-0 top-0 z-30 isolate",
                "box-border h-11 border-b border-r px-3 flex items-center",
                "bg-card",
                "shadow-[2px_0_0_0_rgba(0,0,0,0.10)]",
              )}
            >
              Agent
            </div>

            {days.map((d, idx) => {
              const label = formatDayLabel(d);
              const parts =
                typeof label === "string" ? label.split(" ") : [String(label)];

              const flags = colFlags[idx];

              return (
                <div
                  key={d}
                  className={cn(
                    "sticky top-0 z-20 bg-card",
                    "box-border h-11 border-b border-r px-2",
                    "text-xs text-muted-foreground",
                    "flex flex-col justify-center",
                    flags.weekStart && "border-l-4 border-l-muted-foreground/30",
                    flags.weekend && "bg-muted/30",
                    flags.today && "bg-accent/35 ring-1 ring-inset ring-ring/40",
                  )}
                >
                  {parts.length >= 2 ? (
                    <div className="leading-tight">
                      <div
                        className={cn(
                          "font-medium",
                          flags.today ? "text-foreground" : "text-foreground/80",
                        )}
                      >
                        {parts[0]}
                      </div>
                      <div className="tabular-nums">{parts.slice(1).join(" ")}</div>
                    </div>
                  ) : (
                    <div className="font-medium text-foreground/80 leading-tight">
                      {label}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Body */}
          {rows.map((row) => (
            <div
              key={row.agent.id}
              className="grid group"
              style={{ gridTemplateColumns: gridCols }}
            >
              {/* Sticky agent col */}
              <div
                className={cn(
                  "sticky left-0 z-20 isolate",
                  "box-border h-11 border-b border-r px-3 flex items-center",
                  "bg-card",
                  "shadow-[2px_0_0_0_rgba(0,0,0,0.10)]",
                  "group-hover:bg-accent",
                )}
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className={cn(
                        "w-full h-full bg-inherit",
                        "text-left flex items-center",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm",
                      )}
                      aria-label={`Agent ${row.agent.prenom} ${row.agent.nom}`}
                    >
                      <div className="truncate font-medium leading-none">
                        {row.agent.prenom} {row.agent.nom}
                      </div>
                    </button>
                  </TooltipTrigger>

                  <TooltipContent side="right" align="start" className="max-w-xs">
                    <div className="space-y-1">
                      <div className="text-sm font-medium">
                        {row.agent.prenom} {row.agent.nom}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Code personnel :{" "}
                        <span className="font-medium tabular-nums text-foreground">
                          {row.agent.code_personnel ?? "—"}
                        </span>
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </div>

              {row.days.map((day, idx) => {
                const flags = colFlags[idx];
                const isSelected =
                  selected != null &&
                  selected.agentId === row.agent.id &&
                  selected.dayDate === day.day_date;

                return (
                  <TeamDayCell
                    key={`${row.agent.id}-${day.day_date}`}
                    day={day}
                    selected={isSelected}
                    isWeekStart={flags.weekStart}
                    isWeekend={flags.weekend}
                    isColToday={flags.today}
                    onClick={() => onCellClick(row.agent, day)}
                  />
                );
              })}
            </div>
          ))}

          {rows.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">{emptyLabel}</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
