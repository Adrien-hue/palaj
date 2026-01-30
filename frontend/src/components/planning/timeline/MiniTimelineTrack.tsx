"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useTimelineLanes, type TimelineInputSegment } from "./useTimelineLanes";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type Props<T> = {
  segments: TimelineInputSegment<T>[];
  range: { startMin: number; endMin: number };
  maxLanes?: number; // default 2
  ariaLabel?: string;

  // styling
  className?: string;
  barClassName?: string; // default uses bg-foreground/45
  barStyle?: (s: T) => React.CSSProperties | undefined;

  // tooltip
  getTooltip?: (s: T) => React.ReactNode;
};

export function MiniTimelineTrack<T extends { id: string | number }>({
  segments,
  range,
  maxLanes = 2,
  ariaLabel = "Aperçu",
  className,
  barClassName,
  barStyle,
  getTooltip,
}: Props<T>) {
  const { lanes, laneCount } = useTimelineLanes(segments, range);

  const shownLanes = Math.min(laneCount, maxLanes);
  const height = 6 + shownLanes * 8;
  const rowTop = (lane: number) => 3 + lane * 8;

  return (
    <div className={cn("mt-2", className)}>
      <div
        className={cn(
          "relative w-full rounded-full bg-muted ring-1 ring-border",
          // height is computed, but we keep it inline
        )}
        style={{ height }}
        aria-label={ariaLabel}
      >
        {lanes
          .filter((s) => s.lane < maxLanes)
          .map((s) => {
            const tooltip = getTooltip?.(s);
            const bar = (
              <div
                role="img"
                tabIndex={0}
                aria-label={typeof tooltip === "string" ? tooltip : ariaLabel}
                className={cn(
                  "absolute rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  barClassName ?? "bg-foreground/45"
                )}
                style={{
                  left: `${s.leftPct}%`,
                  width: `${s.widthPct}%`,
                  top: rowTop(s.lane),
                  height: 6,
                  ...(barStyle ? barStyle(s) : null),
                }}
              />
            );

            return tooltip ? (
              <Tooltip key={String(s.id)}>
                <TooltipTrigger asChild>{bar}</TooltipTrigger>
                <TooltipContent>{tooltip}</TooltipContent>
              </Tooltip>
            ) : (
              <React.Fragment key={String(s.id)}>{bar}</React.Fragment>
            );
          })}

        {laneCount > maxLanes ? (
          <div className="absolute right-2 top-0 flex h-full items-center text-[10px] text-muted-foreground">
            +{laneCount - maxLanes}
          </div>
        ) : null}
      </div>
    </div>
  );
}
