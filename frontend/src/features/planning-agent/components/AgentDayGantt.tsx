"use client";

import { useMemo } from "react";

import type { ShiftSegmentVm } from "@/features/planning-agent/vm/agentPlanning.vm";
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

function segmentsToLanes(
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
    out.push({ ...s, lane });
  }

  return out;
}

export function AgentDayGantt({
  segments,
  posteNameById,
  dayStart = "00:00:00",
  dayEnd = "23:59:00",
}: {
  segments: ShiftSegmentVm[];
  posteNameById: Map<number, string>;
  dayStart?: string;
  dayEnd?: string;
}) {
  const startMin = useMemo(() => timeToMinutes(dayStart), [dayStart]);
  const endMin = useMemo(() => timeToMinutes(dayEnd), [dayEnd]);

  const lanes = useMemo(
    () => segmentsToLanes(segments, startMin, endMin),
    [segments, startMin, endMin]
  );

  const laneCount = useMemo(
    () => lanes.reduce((m, s) => Math.max(m, s.lane + 1), 1),
    [lanes]
  );

  const rowHeight = 20;
  const barHeight = 16;
  const padY = 8;
  const height = padY * 2 + laneCount * rowHeight;

  const topForLane = (lane: number) =>
    padY + lane * rowHeight + (rowHeight - barHeight) / 2;

  const pctFromMinutes = (min: number) => {
    const span = Math.max(1, endMin - startMin);
    const pct = ((min - startMin) / span) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  return (
    <TooltipProvider>
      <div className="mt-3">
        <div className="mb-2 flex justify-between text-[11px] tabular-nums text-[color:var(--app-muted)]">
          <span>{dayStart.slice(0, 5)}</span>
          <span>{dayEnd.slice(0, 5)}</span>
        </div>

        <div
          className="relative w-full rounded-xl bg-[color:var(--app-soft)] ring-1 ring-[color:var(--timeline-tick)]"
          style={{ height }}
          aria-label="Timeline du jour"
        >
          {/* ligne guide au milieu de la 1ère lane */}
          <div
            className="absolute inset-x-0 h-px"
            style={{
              top: topForLane(0) + barHeight / 2,
              backgroundColor: "var(--timeline-tick)",
              opacity: 0.7,
            }}
            aria-hidden="true"
          />

          {/* Repères horaires */}
          {[6, 12, 18].map((h) => {
            const left = pctFromMinutes(h * 60);
            return (
              <div
                key={h}
                className="pointer-events-none absolute top-0 h-full w-px"
                style={{
                  left: `${left}%`,
                  backgroundColor: "var(--timeline-tick)",
                }}
                aria-hidden="true"
              />
            );
          })}

          {lanes.map((seg) => {
            const poste = posteNameById.get(seg.posteId) ?? `Poste #${seg.posteId}`;
            const time = `${seg.start.slice(0, 5)}–${seg.end.slice(0, 5)}`;
            const cont = `${seg.continuesPrev ? "←" : ""}${seg.continuesNext ? "→" : ""}`.trim();

            const tooltipText = [seg.nom, time, "•", poste, cont].filter(Boolean).join(" ");

            return (
              <Tooltip key={seg.key}>
                <TooltipTrigger asChild>
                  <div
                    role="img"
                    tabIndex={0}
                    aria-label={tooltipText}
                    className="absolute flex items-center rounded-xl px-2 text-[11px] font-semibold shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring)]"
                    style={{
                      left: `${seg.left}%`,
                      width: `${seg.width}%`,
                      top: topForLane(seg.lane),
                      height: barHeight,
                      minWidth: 36,
                      backgroundColor: "var(--timeline-bar)",
                      color: "var(--timeline-bar-text)",
                    }}
                  >
                    <div className="min-w-0 truncate leading-none">
                      {seg.nom}
                      {seg.continuesPrev ? " ←" : ""}
                      {seg.continuesNext ? " →" : ""}
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>{tooltipText}</TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
}
