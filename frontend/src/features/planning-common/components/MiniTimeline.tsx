"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type TimelineSegment = {
  id: string | number;
  start: number; // units in the chosen range (ex: minutes)
  end: number;
  variant?: "normal" | "continuation" | "muted";
  title?: string;
};

type Props = {
  segments: TimelineSegment[];
  range?: { min: number; max: number }; // default 0..1440
  className?: string;
  heightClassName?: string; // default "h-1.5"
  maxSegmentsToRender?: number; // default 3
};

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

export function MiniTimeline({
  segments,
  range = { min: 0, max: 24 * 60 },
  className,
  heightClassName = "h-1.5",
  maxSegmentsToRender = 3,
}: Props) {
  const total = range.max - range.min;

  const normalized = React.useMemo(() => {
    if (!segments?.length) return [];

    return segments
      .map((s) => {
        const start = clamp(s.start, range.min, range.max);
        const end = clamp(s.end, range.min, range.max);
        return { ...s, start, end, width: Math.max(0, end - start) };
      })
      .filter((s) => s.width > 0)
      .sort((a, b) => a.start - b.start)
      .slice(0, maxSegmentsToRender);
  }, [segments, range.min, range.max, maxSegmentsToRender]);

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden rounded-full bg-muted",
        heightClassName,
        className
      )}
    >
      {normalized.length === 0 ? (
        <div className="absolute inset-0 rounded-full bg-foreground/20" />
      ) : (
        normalized.map((s) => {
          const leftPct = ((s.start - range.min) / total) * 100;
          const widthPct = (s.width / total) * 100;

          const segClass =
            s.variant === "continuation"
              ? "bg-foreground/25"
              : s.variant === "muted"
              ? "bg-foreground/15"
              : "bg-foreground/45";

          return (
            <div
              key={s.id}
              title={s.title}
              className={cn("absolute top-0 h-full rounded-full", segClass)}
              style={{
                left: `${leftPct}%`,
                width: `${Math.max(2, widthPct)}%`,
              }}
            />
          );
        })
      )}
    </div>
  );
}
