"use client";

import * as React from "react";
import type { AgentDay } from "@/types";
import { cn } from "@/lib/utils";
import { DayTypeBadge } from "@/components/planning/DayTypeBadge";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { formatDateFRLong } from "@/utils/date.format";
import { Badge } from "@/components/ui/badge";

function hhmm(t: string) {
  return (t ?? "").slice(0, 5);
}
function parseHHMMSS(t: string): number {
  const [hh, mm] = t.split(":").map((x) => parseInt(x, 10));
  return hh * 60 + mm;
}
function wrapsMidnight(start: string, end: string) {
  return parseHHMMSS(end) <= parseHHMMSS(start);
}

function TrancheBadge({
  label,
  color,
}: {
  label: string;
  color?: string | null;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border-2 px-2 py-0.5",
        "text-[10px] font-medium leading-none truncate",
        "bg-muted/40 hover:bg-muted/60 transition-colors",
      )}
      style={{ borderColor: color ?? "hsl(var(--border))" }}
      title={label}
    >
      <span
        className="mr-1 inline-block h-2 w-2 rounded-full border"
        style={{ backgroundColor: color ?? "transparent" }}
        aria-hidden="true"
      />
      <span className="truncate">{label}</span>
    </span>
  );
}

function TeamDayCellTooltip({ day }: { day: AgentDay }) {
  const dateLabel = formatDateFRLong(day.day_date);
  const tranches = (day.tranches ?? [])
    .slice()
    .sort((a, b) => a.heure_debut.localeCompare(b.heure_debut));

  const hasTranches = tranches.length > 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-medium">{dateLabel}</div>
        <div className="flex items-center gap-2">
          <DayTypeBadge dayType={day.day_type} />
          {day.is_off_shift ? (
            <Badge variant="secondary" className="h-5 rounded-full px-2 py-0 text-[10px]">
              HS
            </Badge>
          ) : null}
        </div>
      </div>

      {day.description ? (
        <div className="text-xs text-muted-foreground line-clamp-2">
          {day.description}
        </div>
      ) : null}

      {!hasTranches ? (
        <div className="text-xs text-muted-foreground">Aucune tranche.</div>
      ) : (
        <div className="space-y-1">
          {tranches.slice(0, 4).map((tr) => {
            const wrap = wrapsMidnight(tr.heure_debut, tr.heure_fin);
            return (
              <div key={tr.id} className="flex items-center justify-between gap-3">
                <div className="min-w-0 flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full border"
                    style={{ backgroundColor: tr.color ?? "transparent" }}
                    aria-hidden="true"
                  />
                  <span className="truncate text-xs font-medium">{tr.nom}</span>
                </div>

                <div className="shrink-0 flex items-center gap-2 text-[11px] tabular-nums text-muted-foreground">
                  <span>
                    {hhmm(tr.heure_debut)}–{hhmm(tr.heure_fin)}
                  </span>
                  {wrap ? (
                    <Badge variant="outline" className="h-5 rounded-full px-2 py-0 text-[10px]">
                      passe minuit
                    </Badge>
                  ) : null}
                </div>
              </div>
            );
          })}

          {tranches.length > 4 ? (
            <div className="text-[11px] text-muted-foreground">
              +{tranches.length - 4} tranche(s)
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export function TeamDayCell({
  day,
  isWeekStart,
  isWeekend,
  isColToday,
  selected = false,
  onClick,
}: {
  day: AgentDay;
  isWeekStart?: boolean;
  isWeekend?: boolean;
  isColToday?: boolean;
  selected?: boolean;
  onClick?: () => void;
}) {
  const t = day.day_type;

  const tranches = day.tranches ?? [];
  const hasWork = tranches.length > 0;

  const button = (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "box-border h-11 w-[80px] px-2 py-1.5 text-left overflow-hidden",
        "cursor-pointer select-none",
        "border-b border-r",
        isWeekStart && "border-l-4 border-l-muted-foreground/30",
        isWeekend && "bg-muted/20",

        isColToday && !selected && "bg-accent/25 ring-1 ring-inset ring-ring/30",
        selected && "bg-accent/40 ring-2 ring-ring z-20",

        "hover:bg-muted/30",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "transition-colors",
      )}
    >
      <div className="flex min-h-0 items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {t === "working" || hasWork ? (
            <div className="space-y-1.5">
              {t !== "working" ? (
                <DayTypeBadge dayType={t} />
              ) : (
                <div className="flex flex-wrap gap-1">
                  {tranches.slice(0, 2).map((tr) => (
                    <TrancheBadge key={tr.id} label={tr.nom} color={tr.color} />
                  ))}
                  {tranches.length > 2 ? (
                    <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] text-muted-foreground bg-muted/30">
                      +{tranches.length - 2}
                    </span>
                  ) : null}
                </div>
              )}
            </div>
          ) : (
            <DayTypeBadge dayType={t} />
          )}
        </div>

        {day.is_off_shift ? (
          <span className="text-[10px] text-muted-foreground shrink-0">HS</span>
        ) : null}
      </div>
    </button>
  );

  const hasDescription = (day.description ?? "").trim().length > 0;

  const shouldShowTooltip =
    day.day_type === "working" ||
    hasWork ||
    hasDescription ||
    !!day.is_off_shift;

  if (!shouldShowTooltip) return button;

  return (
    <Tooltip delayDuration={150}>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent side="top" align="start" className="w-80">
        <TeamDayCellTooltip day={day} />
      </TooltipContent>
    </Tooltip>
  );
}
