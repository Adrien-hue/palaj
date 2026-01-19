export function normalizeDesc(desc?: string | null) {
  const v = (desc ?? "").trim();
  return v.length ? v : null;
}
