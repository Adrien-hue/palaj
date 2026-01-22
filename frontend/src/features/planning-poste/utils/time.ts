export function timeHHMM(t: string) {
  return (t ?? "").slice(0, 5);
}

export function parseTimeToMinutes(t: string) {
  // expects "HH:MM:SS" or "HH:MM"
  const hh = Number(t.slice(0, 2));
  const mm = Number(t.slice(3, 5));
  return hh * 60 + mm;
}

export function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}
