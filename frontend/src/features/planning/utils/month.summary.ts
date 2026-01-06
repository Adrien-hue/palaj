import type { ShiftSegmentVm } from "@/features/planning/vm/planning.vm";
import { parseTimeToMinutes } from "@/features/planning/utils/planning.utils";

type Window = { start: string; end: string };

export function buildTimeWindows(
  segments: ShiftSegmentVm[],
  gapThresholdMinutes = 60 // au-delà => nouvelle fenêtre
): Window[] {
  if (segments.length === 0) return [];

  const sorted = [...segments].sort((a, b) => a.start.localeCompare(b.start));

  const windows: Window[] = [];
  let curStart = sorted[0].start;
  let curEnd = sorted[0].end;

  for (let i = 1; i < sorted.length; i++) {
    const prevEndMin = parseTimeToMinutes(curEnd);
    const nextStartMin = parseTimeToMinutes(sorted[i].start);

    // si ça chevauche ou ça continue (gap <= threshold), on étend la fenêtre
    if (nextStartMin <= prevEndMin + gapThresholdMinutes) {
      // end = max(curEnd, next.end)
      const nextEnd = sorted[i].end;
      if (parseTimeToMinutes(nextEnd) > parseTimeToMinutes(curEnd)) curEnd = nextEnd;
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
  const shown = windows.slice(0, max).map(w => `${w.start.slice(0,5)}–${w.end.slice(0,5)}`);
  const more = windows.length - shown.length;
  return more > 0 ? `${shown.join(", ")} +${more}` : shown.join(", ");
}
