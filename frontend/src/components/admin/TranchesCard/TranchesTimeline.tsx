"use client";

import * as React from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import type { TranchesTimelineProps } from "./types";
import { formatHHMM, trancheToSegments } from "./helpers";

const TOTAL_MINUTES = 1440;
const LANES = 4;
const LANE_HEIGHT = 16;

export default function TranchesTimeline({
  tranches,
  markerEveryHours = 3,
  onSelectTranche,
}: TranchesTimelineProps) {
  const trackHeight = LANES * LANE_HEIGHT;

  const markers = React.useMemo(() => {
    const res: number[] = [];
    for (let h = 0; h <= 24; h += markerEveryHours) res.push(h);
    return res;
  }, [markerEveryHours]);

  const [hoveredId, setHoveredId] = React.useState<number | null>(null);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Timeline (24h)</CardTitle>
        <p className="text-xs text-muted-foreground">
          Survolez une tranche pour voir les heures exactes, cliquez pour la
          sélectionner.
        </p>
      </CardHeader>

      <CardContent className="pt-0">
        {/* top labels */}
        <div className="relative h-6">
          {markers.map((h) => {
            const leftPct = (h * 60 * 100) / TOTAL_MINUTES;
            const label = `${String(h).padStart(2, "0")}:00`;
            return (
              <div
                key={h}
                className="absolute top-0"
                style={{ left: `${leftPct}%` }}
              >
                <div className="-translate-x-1/2 text-[10px] font-medium text-muted-foreground">
                  {label}
                </div>
              </div>
            );
          })}
        </div>

        {/* track */}
        <div
          className="relative w-full overflow-hidden rounded-lg border bg-background"
          style={{ height: `${trackHeight}px` }}
          onMouseLeave={() => setHoveredId(null)}
        >
          {/* vertical grid */}
          {markers.map((h) => {
            const leftPct = (h * 60 * 100) / TOTAL_MINUTES;
            return (
              <div
                key={`grid-${h}`}
                className="absolute top-0 h-full w-px bg-border"
                style={{ left: `${leftPct}%` }}
              />
            );
          })}

          {/* bars */}
          {tranches.flatMap((t, idx) => {
            const lane = idx % LANES;
            const top = lane * LANE_HEIGHT + 2;

            const segments = trancheToSegments(t.heure_debut, t.heure_fin);
            const tooltipText = `${t.nom} — ${formatHHMM(
              t.heure_debut
            )} → ${formatHHMM(t.heure_fin)}`;

            const isHovered = hoveredId === t.id;
            const isDimmed = hoveredId !== null && hoveredId !== t.id;

            return segments.map((seg, segIdx) => {
              const leftPct = (seg.startMin * 100) / TOTAL_MINUTES;
              const widthPct =
                ((seg.endMin - seg.startMin) * 100) / TOTAL_MINUTES;

              return (
                <Tooltip key={`${t.id}-${segIdx}`} delayDuration={120}>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className={[
                        "absolute text-left",
                        isHovered ? "z-20" : "z-10",
                        isDimmed ? "opacity-40" : "opacity-100",
                      ].join(" ")}
                      style={{
                        top: `${top}px`,
                        left: `${leftPct}%`,
                        width: `${widthPct}%`,
                      }}
                      onClick={() => onSelectTranche?.(t.id)}
                      onMouseEnter={() => setHoveredId(t.id)}
                      onFocus={() => setHoveredId(t.id)}
                      onBlur={() => setHoveredId((cur) => (cur === t.id ? null : cur))}
                      aria-label={tooltipText}
                      title={tooltipText}
                    >
                      <div
                        className={[
                          "h-3 rounded-md px-1 text-[10px] font-medium text-primary-foreground",
                          "bg-primary/80 ring-1 ring-primary/10 shadow-sm transition",
                          isHovered
                            ? "bg-primary ring-2 ring-ring shadow-md scale-[1.03]"
                            : "",
                        ].join(" ")}
                      >
                        <div className="truncate leading-3">{t.nom}</div>
                      </div>
                    </button>
                  </TooltipTrigger>

                  <TooltipContent side="top" align="center">
                    <div className="text-xs">{tooltipText}</div>
                  </TooltipContent>
                </Tooltip>
              );
            });
          })}
        </div>
      </CardContent>
    </Card>
  );
}
