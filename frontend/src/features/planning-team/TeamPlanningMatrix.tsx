"use client";

import * as React from "react";
import type { Agent, AgentDay, TeamAgentPlanning } from "@/types";
import { cn } from "@/lib/utils";
import { DayCell } from "./DayCell";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

import { isWeekend, toISODate, addDaysISO } from "@/utils/date.format";

type Props = {
  days: string[];
  rows: TeamAgentPlanning[];
  loading?: boolean;
  emptyLabel?: string;

  formatDayLabel: (isoDate: string) => string;
  onCellClick: (agent: Agent, day: AgentDay, segments: CellSegment[]) => void;
};

const AGENT_COL_W = 260;
const DAY_COL_W = 140;

function isMonday(isoDate: string) {
  return new Date(isoDate + "T00:00:00").getDay() === 1;
}

function parseHHMMSS(t: string): number {
  // "06:15:00" -> minutes since 00:00
  const [hh, mm] = t.split(":").map((x) => parseInt(x, 10));
  return hh * 60 + mm;
}

type CellSegment = {
  id: string;
  label: string;
  startMin: number;
  endMin: number;
  isContinuation?: boolean;
};

function mkSegment(
  id: string,
  label: string,
  startMin: number,
  endMin: number,
  opts?: { continuation?: boolean }
): CellSegment {
  return {
    id,
    label,
    startMin,
    endMin,
    isContinuation: opts?.continuation ?? false,
  };
}

export function TeamPlanningMatrix({
  days,
  rows,
  loading,
  emptyLabel = "Aucun agent dans cette équipe.",
  formatDayLabel,
  onCellClick,
}: Props) {

  const gridCols = React.useMemo(
    () => `${AGENT_COL_W}px repeat(${days.length || 28}, ${DAY_COL_W}px)`,
    [days.length]
  );

  const headerDays = days.length
    ? days
    : Array.from({ length: 28 }).map((_, i) => `D${i + 1}`);

  const todayISO = React.useMemo(() => toISODate(new Date()), []);

  const colFlags = React.useMemo(() => {
    if (!days.length) {
      return headerDays.map(() => ({
        weekStart: false,
        weekend: false,
        today: false,
      }));
    }

    return days.map((d) => ({
      weekStart: isMonday(d),
      weekend: isWeekend(d),
      today: d === todayISO,
    }));
  }, [days, days.length, headerDays, todayISO]);

  return (
    <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
      <div className="overflow-auto">
        <div className="min-w-max">
          {/* Header row */}
          <div className="grid" style={{ gridTemplateColumns: gridCols }}>
            {/* Sticky corner */}
            <div
              className={cn(
                "sticky left-0 top-0 z-30 isolate",
                "box-border border-b border-r px-3 h-11 flex items-center",
                "bg-card",
                "shadow-[2px_0_0_0_rgba(0,0,0,0.10)]"
              )}
            >
              Agent
            </div>

            {headerDays.map((d, idx) => {
              const label = days.length ? formatDayLabel(d) : d;
              const parts =
                typeof label === "string" ? label.split(" ") : [String(label)];

              const flags = colFlags[idx] ?? {
                weekStart: false,
                weekend: false,
                today: false,
              };

              return (
                <div
                  key={d}
                  className={cn(
                    "sticky top-0 z-20",
                    "bg-card",
                    "box-border h-11 border-b border-r px-2 text-xs text-muted-foreground",
                    "flex flex-col justify-center",
                    flags.weekStart && "border-l-4 border-l-muted-foreground/30",
                    flags.weekend && "bg-muted/30",
                    flags.today && "bg-accent/35 ring-1 ring-inset ring-ring/40"
                  )}
                >
                  {parts.length >= 2 ? (
                    <div className="leading-tight">
                      <div
                        className={cn(
                          "font-medium",
                          flags.today ? "text-foreground" : "text-foreground/80"
                        )}
                      >
                        {parts[0]}
                      </div>
                      <div className="tabular-nums">
                        {parts.slice(1).join(" ")}
                      </div>
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
          {rows.map((row) => {
            // Build overlay segments (including continuations on J+1) for THIS agent row
            const segmentsByDate = (() => {
              const map = new Map<string, CellSegment[]>();

              // init keys so we only draw within the window
              for (const d of row.days) {
                map.set(d.day_date, []);
              }

              for (const d of row.days) {
                const date = d.day_date;

                for (const tr of d.tranches ?? []) {
                  const start = parseHHMMSS(tr.heure_debut);
                  const end = parseHHMMSS(tr.heure_fin);

                  if (end > start) {
                    // normal segment on same day
                    map.get(date)?.push(
                      mkSegment(`tr-${tr.id}-${date}`, tr.nom, start, end)
                    );
                  } else {
                    // wraps midnight: split into two segments
                    map.get(date)?.push(
                      mkSegment(`tr-${tr.id}-${date}-A`, tr.nom, start, 24 * 60)
                    );

                    const nextDate = addDaysISO(date, 1);
                    if (map.has(nextDate)) {
                      map.get(nextDate)?.push(
                        mkSegment(
                          `tr-${tr.id}-${nextDate}-B`,
                          tr.nom,
                          0,
                          end,
                          { continuation: true }
                        )
                      );
                    }
                  }
                }
              }

              // stable order per cell
              for (const [k, arr] of map.entries()) {
                arr.sort((a, b) => a.startMin - b.startMin);
                map.set(k, arr);
              }

              return map;
            })();

            return (
              <div
                key={row.agent.id}
                className={cn("grid group")}
                style={{
                  gridTemplateColumns: `${AGENT_COL_W}px repeat(${days.length}, ${DAY_COL_W}px)`,
                }}
              >
                {/* Sticky agent col */}
                <div
                  className={cn(
                    "sticky left-0 z-20 isolate",
                    "box-border border-b border-r px-3 h-11 flex items-center",
                    "bg-card",
                    "shadow-[2px_0_0_0_rgba(0,0,0,0.10)]",
                    "group-hover:bg-accent"
                  )}
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className={cn(
                          "w-full h-full bg-inherit",
                          "text-left flex items-center",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
                        )}
                        aria-label={`Agent ${row.agent.prenom} ${row.agent.nom}`}
                      >
                        <div className="font-medium leading-none truncate">
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
                  const flags = colFlags[idx] ?? {
                    weekStart: false,
                    weekend: false,
                    today: false,
                  };

                  const segments = segmentsByDate.get(day.day_date) ?? [];

                  return (
                    <DayCell
                      key={`${row.agent.id}-${day.day_date}`}
                      day={day}
                      segments={segments}
                      isWeekStart={flags.weekStart}
                      isWeekend={flags.weekend}
                      isColToday={flags.today}
                      onClick={() => {
                        onCellClick(row.agent, day, segments);
                      }}
                    />
                  );
                })}
              </div>
            );
          })}

          {!loading && rows.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">{emptyLabel}</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
