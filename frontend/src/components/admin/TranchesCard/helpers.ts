// frontend/src/components/admin/TranchesCard/helpers.ts
import { TrancheSegment } from "./types";

export function toTimeInput(apiTime?: string | null) {
  // "06:00:00" -> "06:00"
  if (!apiTime) return "";
  return apiTime.slice(0, 5);
}

export function toApiTime(inputTime?: string | null) {
  // "06:00" -> "06:00:00"
  if (!inputTime) return "";
  return inputTime.length === 5 ? `${inputTime}:00` : inputTime;
}

export function isValidTimeHHMM(v: string) {
  return /^\d{2}:\d{2}$/.test(v);
}

export function formatRange(heureDebut?: string | null, heureFin?: string | null) {
  const s = toTimeInput(heureDebut);
  const e = toTimeInput(heureFin);
  if (!s || !e) return "—";
  return `${s} → ${e}`;
}

export function timeToMinutes(apiTime: string) {
  // expects "HH:MM:SS" or "HH:MM"
  const hh = Number(apiTime.slice(0, 2));
  const mm = Number(apiTime.slice(3, 5));
  if (Number.isNaN(hh) || Number.isNaN(mm)) return 0;
  return hh * 60 + mm;
}

export function formatHHMM(apiTime?: string | null) {
  if (!apiTime) return "—";
  return apiTime.slice(0, 5);
}

export function trancheToSegments(heureDebut: string, heureFin: string): TrancheSegment[] {
  const start = timeToMinutes(heureDebut);
  const end = timeToMinutes(heureFin);

  // same day
  if (end > start) return [{ startMin: start, endMin: end }];

  // crosses midnight or equal => split
  // ex: 22:00 -> 06:00  => [22:00->24:00] + [00:00->06:00]
  if (end < start) {
    return [
      { startMin: start, endMin: 1440 },
      { startMin: 0, endMin: end },
    ];
  }

  // end === start : treat as full day? (rare). We'll show nothing or full-day
  // Here: show full-day for visibility
  return [{ startMin: 0, endMin: 1440 }];
}
