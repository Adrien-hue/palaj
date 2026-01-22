"use client";

import { useMemo } from "react";

import type { ShiftSegmentVm } from "../vm/agentPlanning.vm";
import { timeToMinutes } from "@/utils/time.format";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

type LaneSeg = ShiftSegmentVm & {
  left: number;
  width: number;
  lane: number;
  startMin: number;
  endMin: number;
};

function packLanes(
  segments: ShiftSegmentVm[],
  startMin: number,
  endMin: number
): LaneSeg[] {
  const span = Math.max(1, endMin - startMin);

  const segs = segments
    .map((s) => {
      const sMin = clamp(timeToMinutes(s.start), startMin, endMin);
      const eMin = clamp(timeToMinutes(s.end), startMin, endMin);
      const left = ((sMin - startMin) / span) * 100;
      const width = ((eMin - sMin) / span) * 100;
      return { ...s, left, width, startMin: sMin, endMin: eMin };
    })
    .filter((s) => s.width > 0.1)
    .sort((a, b) => a.start.localeCompare(b.start));

  const lanesEnd: number[] = [];
  const out: LaneSeg[] = [];

  for (const s of segs) {
    let lane = lanesEnd.findIndex((end) => end <= s.startMin);
    if (lane === -1) {
      lane = lanesEnd.length;
      lanesEnd.push(s.endMin);
    } else {
      lanesEnd[lane] = s.endMin;
    }
    out.push({ ...s, lane } as LaneSeg);
  }

  return out;
}

export function AgentMiniGantt({
  segments,
  dayStart = "00:00:00",
  dayEnd = "24:00:00",
  maxLanes = 2,
}: {
  segments: ShiftSegmentVm[];
  dayStart?: string;
  dayEnd?: string;
  maxLanes?: number;
}) {
  const startMin = useMemo(() => timeToMinutes(dayStart), [dayStart]);
  const endMin = useMemo(() => timeToMinutes(dayEnd), [dayEnd]);

  const lanes = useMemo(
    () => packLanes(segments, startMin, endMin),
    [segments, startMin, endMin]
  );

  const laneCount = useMemo(
    () => lanes.reduce((m, s) => Math.max(m, s.lane + 1), 1),
    [lanes]
  );

  const shownLanes = Math.min(laneCount, maxLanes);
  const height = 6 + shownLanes * 8;
  const rowTop = (lane: number) => 3 + lane * 8;

  return (
    <TooltipProvider>
      <div className="mt-2">
        <div
          className="relative w-full rounded-full bg-[color:var(--app-soft)] ring-1 ring-[color:var(--timeline-tick)]"
          style={{ height }}
          aria-label="Aperçu des tranches"
        >
          {lanes
            .filter((s) => s.lane < maxLanes)
            .map((s) => {
              const time = `${s.start.slice(0, 5)}–${s.end.slice(0, 5)}`;
              const tooltipText = `${s.nom} • ${time}`;

              return (
                <Tooltip key={s.key}>
                  <TooltipTrigger asChild>
                    <div
                      role="img"
                      tabIndex={0}
                      aria-label={tooltipText}
                      className="absolute rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring)]"
                      style={{
                        left: `${s.left}%`,
                        width: `${s.width}%`,
                        top: rowTop(s.lane),
                        height: 6,
                        backgroundColor: "var(--timeline-bar)",
                      }}
                    />
                  </TooltipTrigger>
                  <TooltipContent>{tooltipText}</TooltipContent>
                </Tooltip>
              );
            })}

          {laneCount > maxLanes ? (
            <div className="absolute right-2 top-0 flex h-full items-center text-[10px] text-[color:var(--app-muted)]">
              +{laneCount - maxLanes}
            </div>
          ) : null}
        </div>
      </div>
    </TooltipProvider>
  );
}
