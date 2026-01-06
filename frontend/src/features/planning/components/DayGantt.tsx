import type { ShiftSegmentVm } from "@/features/planning/vm/planning.vm";
import { parseTimeToMinutes } from "../utils/planning.utils";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

type LaneSeg = ShiftSegmentVm & { left: number; width: number; lane: number };

function segmentsToLanes(
  segments: ShiftSegmentVm[],
  startMin: number,
  endMin: number
): LaneSeg[] {
  const segs = segments
    .map((s) => {
      const sMin = clamp(parseTimeToMinutes(s.start), startMin, endMin);
      const eMin = clamp(parseTimeToMinutes(s.end), startMin, endMin);
      const span = Math.max(1, endMin - startMin);
      const left = ((sMin - startMin) / span) * 100;
      const width = ((eMin - sMin) / span) * 100;
      return { ...s, left, width };
    })
    .filter((s) => s.width > 0.1)
    .sort((a, b) => a.start.localeCompare(b.start));

  const lanesEnd: number[] = [];
  const out: LaneSeg[] = [];

  for (const s of segs) {
    const sMin = parseTimeToMinutes(s.start);
    const eMin = parseTimeToMinutes(s.end);

    let lane = lanesEnd.findIndex((end) => end <= sMin);
    if (lane === -1) {
      lane = lanesEnd.length;
      lanesEnd.push(eMin);
    } else {
      lanesEnd[lane] = eMin;
    }

    out.push({ ...s, lane });
  }

  return out;
}

export function DayGantt({
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
  const startMin = parseTimeToMinutes(dayStart);
  const endMin = parseTimeToMinutes(dayEnd);

  const lanes = segmentsToLanes(segments, startMin, endMin);
  const laneCount = lanes.reduce((m, s) => Math.max(m, s.lane + 1), 1);

  const rowHeight = 20; // hauteur d'une lane
  const barHeight = 16; // hauteur de la barre
  const padY = 8; // padding haut/bas du container
  const height = padY * 2 + laneCount * rowHeight;

  const topForLane = (lane: number) =>
    padY + lane * rowHeight + (rowHeight - barHeight) / 2;

  const pctFromMinutes = (min: number, startMin: number, endMin: number) => {
    const span = Math.max(1, endMin - startMin);
    const pct = ((min - startMin) / span) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  return (
    <div className="mt-3">
      <div className="mb-2 flex justify-between text-[11px] text-muted-foreground tabular-nums">
        <span>{dayStart.slice(0, 5)}</span>
        <span>{dayEnd.slice(0, 5)}</span>
      </div>

      <div
        className="relative w-full rounded-2xl bg-muted ring-1 ring-border"
        style={{ height }}
      >
        {/* ligne guide au milieu de la 1ère lane */}
        <div
          className="absolute inset-x-0 h-px bg-border/60"
          style={{ top: topForLane(0) + barHeight / 2 }}
        />

        {/* Repères horaires */}
        {[6, 12, 18].map((h) => {
          const left = pctFromMinutes(h * 60, startMin, endMin);
          return (
            <div
              key={h}
              className="pointer-events-none absolute top-0 h-full w-px"
              style={{
                left: `${left}%`,
                backgroundColor: "var(--timeline-tick)",
              }}
            />
          );
        })}

        {lanes.map((seg) => {
          const poste =
            posteNameById.get(seg.posteId) ?? `Poste #${seg.posteId}`;

          return (
            <div
              key={seg.key}
              className="absolute flex items-center rounded-xl px-2 text-[11px] font-semibold shadow-sm"
              style={{
                left: `${seg.left}%`,
                width: `${seg.width}%`,
                top: topForLane(seg.lane),
                height: barHeight,
                minWidth: 36,
                backgroundColor: "var(--timeline-bar)",
                color: "var(--timeline-bar-text)",
              }}
              title={`${seg.nom} ${seg.start.slice(0, 5)}-${seg.end.slice(
                0,
                5
              )}\n${poste}`}
            >
              <div className="min-w-0 truncate leading-none">
                {seg.nom}
                {seg.continuesPrev ? " ←" : ""}
                {seg.continuesNext ? " →" : ""}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
