// src/utils/time.format.ts

/**
 * Convertit une valeur horaire en minutes depuis 00:00.
 *
 * Supporte :
 * - "HH:MM" / "HH:MM:SS"
 * - "24:00" / "24:00:00" -> 1440
 * - ISO datetime ("...T...") ou suffixe "Z" (interprété en UTC)
 */
export function timeToMinutes(v: string): number {
  if (!v) return 0;

  // ISO datetime (ends with Z or contains 'T')
  if (v.includes("T") || v.endsWith("Z")) {
    const d = new Date(v);
    const hh = d.getUTCHours();
    const mm = d.getUTCMinutes();
    return hh * 60 + mm;
  }

  // "HH:MM:SS" or "HH:MM"
  const hh = Number(v.slice(0, 2));
  const mm = Number(v.slice(3, 5));

  if (!Number.isFinite(hh) || !Number.isFinite(mm)) return 0;

  // accepte 24:00(:00)
  if (hh === 24) return 24 * 60;

  return hh * 60 + mm;
}

/**
 * Formatte une valeur horaire en "HH:MM".
 * Supporte ISO datetime (...T... ou ...Z) via UTC.
 */
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

/** 125 -> "2h05" */
export function formatMinutes(min: number): string {
  const safe = Math.max(0, Math.floor(min));
  const h = Math.floor(safe / 60);
  const m = safe % 60;
  return `${h}h${String(m).padStart(2, "0")}`;
}
