"use client";

import * as React from "react";
import type { AgentDay } from "@/types";
import { cn } from "@/lib/utils";
import { DayTypeBadge } from "@/components/planning/DayTypeBadge";

import type { RhViolation } from "@/types/rhValidation";
import { TeamDayCellTooltip } from "./TeamDayCellTooltip";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type RhLevel = "error" | "warning" | "info";

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

export function TeamDayCell({
  day,
  isWeekStart,
  isWeekend,
  isColToday,
  selected = false,
  rhLevel = null,
  rhViolations = [],
  onClick,
}: {
  day: AgentDay;
  isWeekStart?: boolean;
  isWeekend?: boolean;
  isColToday?: boolean;
  selected?: boolean;
  rhLevel?: RhLevel | null;

  rhViolations?: RhViolation[];

  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  const t = day.day_type;
  const tranches = day.tranches ?? [];
  const hasWork = tranches.length > 0;

  const rhTone =
    !selected && rhLevel === "error"
      ? "border-l-4 border-l-destructive/70 bg-destructive/5"
      : !selected && rhLevel === "warning"
        ? "border-l-4 border-l-amber-500/70 bg-amber-500/5"
        : null;

  // week start uniquement si pas RH
  const weekStartBorder =
    !rhTone && isWeekStart ? "border-l-4 border-l-muted-foreground/30" : null;

  const hoverBg = selected
    ? "" // on ne change pas le fond en hover quand selected
    : rhLevel === "error"
      ? "hover:bg-destructive/8"
      : rhLevel === "warning"
        ? "hover:bg-amber-500/8"
        : "hover:bg-muted/15";

  const button = (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "relative box-border h-11 w-[80px] px-2 py-1.5 text-left overflow-hidden",
        "cursor-pointer select-none",
        "border-b border-r",
        weekStartBorder,
        rhTone,

        isWeekend && "bg-muted/20",
        isColToday && !selected && "bg-accent/25 ring-1 ring-inset ring-ring/30",
        selected && "bg-primary/10 ring-2 ring-inset ring-primary",

        hoverBg,
        "hover:ring-1 hover:ring-inset hover:ring-ring/20",
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
    day.day_type === "working" || hasWork || hasDescription || !!day.is_off_shift;

  // 🔸 On affiche le tooltip aussi si RH est présent
  const shouldShowRhTooltip = (rhViolations?.length ?? 0) > 0;

  if (!shouldShowTooltip && !shouldShowRhTooltip) return button;

  return (
    <Tooltip delayDuration={150}>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent side="top" align="start" className="w-80">
        <TeamDayCellTooltip day={day} rhViolations={rhViolations ?? []} />
      </TooltipContent>
    </Tooltip>
  );
}
