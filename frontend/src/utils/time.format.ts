export function timeToMinutes(v: string): number {
  if (!v) return 0;

  // ISO datetime (ends with Z or contains 'T')
  if (v.includes("T") || v.endsWith("Z")) {
    const d = new Date(v);
    // On prend l'heure UTC car 'Z' => UTC
    const hh = d.getUTCHours();
    const mm = d.getUTCMinutes();
    return hh * 60 + mm;
  }

  // "HH:MM:SS" or "HH:MM"
  const hh = Number(v.slice(0, 2));
  const mm = Number(v.slice(3, 5));
  return hh * 60 + mm;
}

export function timeLabelHHMM(v: string): string {
  if (!v) return "";
  if (v.includes("T") || v.endsWith("Z")) {
    const d = new Date(v);
    const hh = String(d.getUTCHours()).padStart(2, "0");
    const mm = String(d.getUTCMinutes()).padStart(2, "0");
    return `${hh}:${mm}`;
  }
  return v.slice(0, 5);
}
