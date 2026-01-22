// src/features/planning/utils/month.summary.ts

import { timeToMinutes } from "@/utils/time.format";

type Segment = { start: string; end: string };
type Window = { start: string; end: string };

export function buildTimeWindows<T extends Segment>(
  segments: T[],
  gapThresholdMinutes = 60
): Window[] {
  if (segments.length === 0) return [];

  const sorted = [...segments].sort((a, b) => a.start.localeCompare(b.start));

  const windows: Window[] = [];
  let curStart = sorted[0].start;
  let curEnd = sorted[0].end;

  for (let i = 1; i < sorted.length; i++) {
    const prevEndMin = timeToMinutes(curEnd);
    const nextStartMin = timeToMinutes(sorted[i].start);

    if (nextStartMin <= prevEndMin + gapThresholdMinutes) {
      const nextEnd = sorted[i].end;
      if (timeToMinutes(nextEnd) > timeToMinutes(curEnd)) curEnd = nextEnd;
    } else {
      windows.push({ start: curStart, end: curEnd });
      curStart = sorted[i].start;
      curEnd = sorted[i].end;
    }
  }

  windows.push({ start: curStart, end: curEnd });
  return windows;
}

export function formatWindows(windows: Window[], max = 2): string {
  if (windows.length === 0) return "—";
  const shown = windows
    .slice(0, max)
    .map((w) => `${w.start.slice(0, 5)}–${w.end.slice(0, 5)}`);
  const more = windows.length - shown.length;
  return more > 0 ? `${shown.join(", ")} +${more}` : shown.join(", ");
}
