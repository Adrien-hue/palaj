export const rhValidationPosteDayKey = (
  posteId: number | null,
  day: string | null,
  startDate: string | null,
  endDate: string | null,
  profile: "fast" | "full",
  includeInfo: boolean,
) => {
  if (!posteId || !day || !startDate || !endDate) return null;

  return ["rh-validation", "poste", "day", posteId, day, startDate, endDate, profile, includeInfo] as const;
};
