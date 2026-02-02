"use client";

import { useMemo } from "react";
import type { ShiftSegmentVm } from "../vm/agentPlanning.vm";
import { timeToMinutes } from "@/utils/time.format";
import { MiniTimelineTrack } from "@/components/planning/timeline/MiniTimelineTrack";

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
  const range = useMemo(
    () => ({
      startMin: timeToMinutes(dayStart),
      endMin: timeToMinutes(dayEnd),
    }),
    [dayStart, dayEnd],
  );

  const input = useMemo(
    () =>
      segments.map((s) => ({
        ...s,
        id: s.key,
        startMin: timeToMinutes(s.start),
        endMin: timeToMinutes(s.end),
      })),
    [segments],
  );
  console.log("seg color : ", input.map(s => s.color));
  return (
    <MiniTimelineTrack
      segments={input}
      range={range}
      maxLanes={maxLanes}
      ariaLabel="Aperçu des tranches"
      getTooltip={(s) =>
        `${s.nom} • ${s.start.slice(0, 5)}–${s.end.slice(0, 5)}`
      }
      barStyle={(s) => (s.color ? { backgroundColor: s.color } : undefined)}
      // Optionnel: si tu veux garder le style par défaut quand color absent
      barClassName="bg-foreground/45"
    />
  );
}
