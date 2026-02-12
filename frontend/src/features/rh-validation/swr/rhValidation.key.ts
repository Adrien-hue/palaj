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
