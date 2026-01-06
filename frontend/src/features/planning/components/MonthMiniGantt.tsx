import type { ShiftSegmentVm } from "@/features/planning/vm/planning.vm";
import { parseTimeToMinutes } from "@/features/planning/utils/planning.utils";

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

function packLanes(segments: ShiftSegmentVm[], startMin: number, endMin: number): LaneSeg[] {
  const span = Math.max(1, endMin - startMin);

  const segs = segments
    .map((s) => {
      const sMin = clamp(parseTimeToMinutes(s.start), startMin, endMin);
      const eMin = clamp(parseTimeToMinutes(s.end), startMin, endMin);
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

export function MonthMiniGantt({
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
  const startMin = parseTimeToMinutes(dayStart);
  const endMin = parseTimeToMinutes(dayEnd);

  const lanes = packLanes(segments, startMin, endMin);
  const laneCount = lanes.reduce((m, s) => Math.max(m, s.lane + 1), 1);
  const shownLanes = Math.min(laneCount, maxLanes);

  const height = 6 + shownLanes * 8;
  const rowTop = (lane: number) => 3 + lane * 8;

  return (
    <div className="mt-1">
      <div className="relative w-full rounded-full bg-muted ring-1 ring-border" style={{ height }}>
        {lanes
          .filter((s) => s.lane < maxLanes)
          .map((s) => (
            <div
              key={s.key}
              className="absolute rounded-full"
              style={{
                left: `${s.left}%`,
                width: `${s.width}%`,
                top: rowTop(s.lane),
                height: 6,
                backgroundColor: "var(--timeline-bar)",
                color: "var(--timeline-bar-text)",
              }}
              title={`${s.nom} ${s.start.slice(0, 5)}-${s.end.slice(0, 5)}`}
            />
          ))}

        {laneCount > maxLanes ? (
          <div className="absolute right-2 top-0 flex h-full items-center text-[10px] text-muted-foreground">
            +{laneCount - maxLanes}
          </div>
        ) : null}
      </div>
    </div>
  );
}
