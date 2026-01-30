import { useMemo } from "react";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

export type TimelineRange = { startMin: number; endMin: number };

export type TimelineInputSegment<T> = T & {
  startMin: number; // minutes
  endMin: number;   // minutes
};

export type TimelineLaneSegment<T> = T & {
  lane: number;
  leftPct: number;
  widthPct: number;
  startMin: number;
  endMin: number;
};

export function computeTimelineLanes<T>(
  segments: TimelineInputSegment<T>[],
  range: TimelineRange,
  opts?: {
    minWidthPct?: number; // default 0.1
    sortKey?: (s: TimelineInputSegment<T>) => string | number;
  }
): TimelineLaneSegment<T>[] {
  const minWidthPct = opts?.minWidthPct ?? 0.1;
  const span = Math.max(1, range.endMin - range.startMin);

  const segs = segments
    .map((s) => {
      const sMin = clamp(s.startMin, range.startMin, range.endMin);
      const eMin = clamp(s.endMin, range.startMin, range.endMin);
      const leftPct = ((sMin - range.startMin) / span) * 100;
      const widthPct = ((eMin - sMin) / span) * 100;
      return { ...s, startMin: sMin, endMin: eMin, leftPct, widthPct };
    })
    .filter((s) => s.widthPct > minWidthPct)
    .sort((a, b) => {
      const ka = opts?.sortKey ? opts.sortKey(a) : a.startMin;
      const kb = opts?.sortKey ? opts.sortKey(b) : b.startMin;
      return ka < kb ? -1 : ka > kb ? 1 : 0;
    });

  const lanesEnd: number[] = [];
  const out: TimelineLaneSegment<T>[] = [];

  for (const s of segs) {
    let lane = lanesEnd.findIndex((end) => end <= s.startMin);
    if (lane === -1) {
      lane = lanesEnd.length;
      lanesEnd.push(s.endMin);
    } else {
      lanesEnd[lane] = s.endMin;
    }
    out.push({ ...(s as any), lane });
  }

  return out;
}

export function useTimelineLanes<T>(
  segments: TimelineInputSegment<T>[],
  range: TimelineRange,
  deps: unknown[] = []
) {
  const lanes = useMemo(
    () => computeTimelineLanes(segments, range),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [segments, range.startMin, range.endMin, ...deps]
  );

  const laneCount = useMemo(
    () => lanes.reduce((m, s) => Math.max(m, s.lane + 1), 1),
    [lanes]
  );

  return { lanes, laneCount };
}
