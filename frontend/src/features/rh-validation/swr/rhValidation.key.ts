// frontend/src/features/rh-validation/swr/rhValidation.key.ts
export const rhValidationAgentKey = (
  agentId: number | null,
  startDate: string | null,
  endDate: string | null,
) => {
  if (!agentId || !startDate || !endDate) return null;

  return [
    "rh-validation",
    "agent",
    agentId,
    startDate,
    endDate,
  ] as const;
};


export const rhValidationPosteSummaryKey = (
  posteId: number | null,
  startDate: string | null,
  endDate: string | null,
  profile: string | null,
) => {
  if (!posteId || !startDate || !endDate || !profile) return null;

  return [
    "rh-validation",
    "poste",
    "summary",
    posteId,
    startDate,
    endDate,
    profile,
  ] as const;
};