"use client";

import * as React from "react";
import type { AgentDay } from "@/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { MiniTimeline, type TimelineSegment } from "@/features/planning-common";

export type CellSegment = {
  id: string;
  label: string;
  startMin: number;
  endMin: number;
  isContinuation?: boolean;
};

function DayTypeBadge({ t }: { t: string }) {
  if (t === "zcot")
    return <Badge variant="secondary" className="h-5 px-2 rounded-full text-[11px]">ZCOT</Badge>;
  if (t === "rest")
    return <Badge variant="outline" className="h-5 px-2 rounded-full text-[11px]">RP</Badge>;
  if (t === "absent")
    return <Badge variant="destructive" className="h-5 px-2 rounded-full text-[11px]">ABS</Badge>;
  if (t === "unknown")
    return <span className="text-xs text-muted-foreground">—</span>;
  return <Badge variant="outline" className="h-5 px-2 rounded-full text-[11px]">{t}</Badge>;
}

export function DayCell(props: {
  day: AgentDay;
  segments: CellSegment[];
  isWeekStart?: boolean;
  isWeekend?: boolean;
  isColToday?: boolean;
  onClick?: () => void;
}) {
  const { day, segments, isWeekStart, isWeekend, isColToday, onClick } = props;
  const t = day.day_type;

  const hasWorkOverlay = segments.length > 0;
  const contCount = segments.filter((s) => s.isContinuation).length;

  const timelineSegments: TimelineSegment[] = React.useMemo(() => {
    return (segments ?? []).map((s) => ({
      id: s.id,
      start: s.startMin,
      end: s.endMin,
      variant: s.isContinuation ? "continuation" : "normal",
      title: s.label,
    }));
  }, [segments]);

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "box-border h-11 w-[140px] px-2 py-1.5 text-left overflow-hidden",
        "cursor-pointer select-none",
        "border-b border-r",
        isWeekStart && "border-l-4 border-l-muted-foreground/30",
        isWeekend && "bg-muted/20",
        isColToday && "bg-accent/25 ring-1 ring-inset ring-ring/30",
        "hover:bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      )}
    >
      <div className="flex min-h-0 items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {(t === "working" || hasWorkOverlay) ? (
            <div className="space-y-1.5">
              <MiniTimeline
                segments={timelineSegments}
                range={{ min: 0, max: 24 * 60 }}
                heightClassName="h-1.5"
              />

              {t !== "working" ? (
                <div className="flex items-center justify-between gap-2">
                  <DayTypeBadge t={t} />
                  {contCount > 0 ? (
                    <span className="text-[10px] text-muted-foreground shrink-0">
                      ↩︎ descente de nuit
                    </span>
                  ) : null}
                </div>
              ) : (
                <div className="space-y-0.5">
                  {(day.tranches ?? []).slice(0, 2).map((tr) => (
                    <div key={tr.id} className="flex items-center gap-1.5 min-w-0">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-foreground/70 shrink-0" />
                      <span className="text-xs font-medium truncate">{tr.nom}</span>
                    </div>
                  ))}
                  {(day.tranches?.length ?? 0) > 2 ? (
                    <div className="text-[11px] text-muted-foreground">
                      +{(day.tranches?.length ?? 0) - 2}
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          ) : (
            <DayTypeBadge t={t} />
          )}
        </div>

        {day.is_off_shift ? (
          <span className="text-[10px] text-muted-foreground shrink-0">HS</span>
        ) : null}
      </div>
    </button>
  );
}
