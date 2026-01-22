import { useMemo } from "react";

import { timeToMinutes, timeLabelHHMM } from "@/utils/time.format";
import type { PosteShiftSegmentVm } from "@/features/planning-poste/vm/postePlanning.vm";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

type LaneSeg = PosteShiftSegmentVm & {
  left: number;
  width: number;
  lane: number;
  startMin: number;
  endMin: number;
};

function packLanes(
  segments: PosteShiftSegmentVm[],
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

export function PosteMiniGantt({
  segments,
  dayStart = "00:00:00",
  dayEnd = "23:59:59",
  maxLanes = 2,
}: {
  segments: PosteShiftSegmentVm[];
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
          className="relative w-full rounded-full bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]"
          style={{ height }}
          aria-label="Tranches de couverture"
        >
          {lanes
            .filter((s) => s.lane < maxLanes)
            .map((s) => {
              const agentName = `${s.agent.prenom} ${s.agent.nom}`;
              const time = `${timeLabelHHMM(s.start)}–${timeLabelHHMM(s.end)}`;
              const cont = `${s.continuesPrev ? "↤" : ""}${s.continuesNext ? "↦" : ""}`.trim();

              const tooltipText = [s.nom, time, "•", agentName, cont]
                .filter(Boolean)
                .join(" ");

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
