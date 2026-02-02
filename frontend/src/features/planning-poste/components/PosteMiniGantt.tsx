import { useMemo } from "react";
import { timeToMinutes, timeLabelHHMM } from "@/utils/time.format";
import type { PosteShiftSegmentVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { MiniTimelineTrack } from "@/components/planning/timeline/MiniTimelineTrack";

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
  const range = useMemo(
    () => ({ startMin: timeToMinutes(dayStart), endMin: timeToMinutes(dayEnd) }),
    [dayStart, dayEnd]
  );

  const input = useMemo(
    () =>
      segments.map((s) => ({
        ...s,
        id: s.key,
        startMin: timeToMinutes(s.start),
        endMin: timeToMinutes(s.end),
      })),
    [segments]
  );

  return (
    <MiniTimelineTrack
      segments={input}
      range={range}
      maxLanes={maxLanes}
      ariaLabel="Tranches de couverture"
      getTooltip={(s) => {
        const agentName = `${s.agent.prenom} ${s.agent.nom}`;
        const time = `${timeLabelHHMM(s.start)}–${timeLabelHHMM(s.end)}`;
        const cont = `${s.continuesPrev ? "↤" : ""}${s.continuesNext ? "↦" : ""}`.trim();
        return [s.nom, time, "•", agentName, cont].filter(Boolean).join(" ");
      }}
      barStyle={(s) => (s.color ? { backgroundColor: s.color } : undefined)}
      barClassName="bg-foreground/45"
    />
  );
}
