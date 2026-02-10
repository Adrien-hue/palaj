"use client";

import { useMemo } from "react";
import type { ShiftSegmentVm } from "@/features/planning-agent/vm/agentPlanning.vm";
import { timeToMinutes } from "@/utils/time.format";
import { DayTimeline } from "@/components/planning/timeline/DayTimeline";
import { usePosteNamesById } from "@/features/postes/hooks/usePosteNamesById";

export function AgentDayGantt({
  segments,
  dayStart = "00:00:00",
  dayEnd = "23:59:00",
}: {
  segments: ShiftSegmentVm[];
  dayStart?: string;
  dayEnd?: string;
}) {
  const range = useMemo(
    () => ({
      startMin: timeToMinutes(dayStart),
      endMin: timeToMinutes(dayEnd),
    }),
    [dayStart, dayEnd]
  );

  const input = useMemo(
    () =>
      segments.map((s) => ({
        ...s,
        startMin: timeToMinutes(s.start),
        endMin: timeToMinutes(s.end),
      })),
    [segments]
  );

  // ✅ ids postes depuis les segments
  const posteIds = useMemo(() => segments.map((s) => s.posteId), [segments]);
  const { posteNameById } = usePosteNamesById(posteIds);

  return (
    <DayTimeline
      segments={input}
      range={range}
      startLabel={dayStart.slice(0, 5)}
      endLabel={dayEnd.slice(0, 5)}
      getId={(s) => s.key}
      getLabel={(s) =>
        `${s.nom}${s.continuesPrev ? " ←" : ""}${s.continuesNext ? " →" : ""}`
      }
      getTooltip={(s) => {
        const poste = posteNameById.get(s.posteId) ?? `Poste #${s.posteId}`;
        const time = `${s.start.slice(0, 5)}–${s.end.slice(0, 5)}`;
        const cont =
          `${s.continuesPrev ? "←" : ""}${s.continuesNext ? "→" : ""}`.trim();
        return [s.nom, time, "•", poste, cont].filter(Boolean).join(" ");
      }}
      barClassName={() => "bg-primary text-primary-foreground"}
      barStyle={(s) =>
        s.color
          ? {
              backgroundColor: s.color,
            }
          : undefined
      }
    />
  );
}
