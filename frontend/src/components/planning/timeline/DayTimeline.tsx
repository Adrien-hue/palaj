"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  useTimelineLanes,
  type TimelineInputSegment,
} from "./useTimelineLanes";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type Props<T> = {
  segments: TimelineInputSegment<T>[];
  range: { startMin: number; endMin: number };
  startLabel?: string;
  endLabel?: string;

  ticksHours?: number[]; // default [6,12,18]
  className?: string;

  getId: (s: T) => string | number;
  getLabel: (s: T) => string;
  getTooltip?: (s: T) => React.ReactNode;
  barClassName?: (s: T) => string;
  barStyle?: (s: T) => React.CSSProperties | undefined;
  onBarClick?: (s: T) => void;

  textClassName?: (s: T) => string;
  minBarWidthPx?: number; // default 36
};

export function DayTimeline<T>({
  segments,
  range,
  startLabel,
  endLabel,
  ticksHours = [6, 12, 18],
  className,

  getId,
  getLabel,
  getTooltip,
  barClassName,
  barStyle,
  onBarClick,
  textClassName,
  minBarWidthPx = 36,
}: Props<T>) {
  const { lanes, laneCount } = useTimelineLanes(segments, range);

  const rowHeight = 20;
  const barHeight = 16;
  const padY = 8;
  const height = padY * 2 + laneCount * rowHeight;

  const topForLane = (lane: number) =>
    padY + lane * rowHeight + (rowHeight - barHeight) / 2;

  const pctFromMinutes = (min: number) => {
    const span = Math.max(1, range.endMin - range.startMin);
    const pct = ((min - range.startMin) / span) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  return (
    <div className={cn("mt-3", className)}>
      {startLabel && endLabel ? (
        <div className="mb-2 flex justify-between text-[11px] tabular-nums text-muted-foreground">
          <span>{startLabel}</span>
          <span>{endLabel}</span>
        </div>
      ) : null}

      <div
        className="relative w-full rounded-xl bg-muted ring-1 ring-border"
        style={{ height }}
        aria-label="Timeline"
      >
        {/* guide */}
        <div
          className="absolute inset-x-0 h-px bg-border/70"
          style={{ top: topForLane(0) + barHeight / 2 }}
          aria-hidden="true"
        />

        {/* ticks */}
        {ticksHours.map((h) => {
          const left = pctFromMinutes(h * 60);
          return (
            <div
              key={h}
              className="pointer-events-none absolute top-0 h-full w-px bg-border"
              style={{ left: `${left}%` }}
              aria-hidden="true"
            />
          );
        })}

        {lanes.map((seg) => {
          const tooltip = getTooltip?.(seg as any);
          const label = getLabel(seg as any);

          const bar = (
            <div
              role={onBarClick ? "button" : "img"}
              tabIndex={0}
              aria-label={typeof tooltip === "string" ? tooltip : label}
              className={cn(
                "absolute flex items-center rounded-xl px-2 text-[11px] font-semibold shadow-sm",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                onBarClick && "cursor-pointer hover:brightness-95",
                barClassName
                  ? barClassName(seg as any)
                  : "bg-foreground/60 text-background",
              )}
              style={{
                left: `${seg.leftPct}%`,
                width: `${seg.widthPct}%`,
                top: topForLane(seg.lane),
                height: barHeight,
                minWidth: minBarWidthPx,
                ...(barStyle ? barStyle(seg as any) : null),
              }}
              onClick={onBarClick ? () => onBarClick(seg as any) : undefined}
              onKeyDown={
                onBarClick
                  ? (e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        onBarClick(seg as any);
                      }
                    }
                  : undefined
              }
            >
              <div
                className={cn(
                  "min-w-0 truncate leading-none",
                  textClassName?.(seg as any),
                )}
              >
                {label}
              </div>
            </div>
          );

          return tooltip ? (
            <Tooltip key={String(getId(seg as any))}>
              <TooltipTrigger asChild>{bar}</TooltipTrigger>
              <TooltipContent>{tooltip}</TooltipContent>
            </Tooltip>
          ) : (
            <React.Fragment key={String(getId(seg as any))}>
              {bar}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
