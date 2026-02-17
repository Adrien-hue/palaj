import type { RhViolation } from "@/types/rhValidation";

export type RhViolationContext =
  | { kind: "agent"; agent_id: number; label: string }
  | { kind: "poste"; poste_id: number; label: string }
  | { kind: "team"; team_id: number; label: string }
  | { kind: "none" };

export type RhViolationOccurrence = {
  violation: RhViolation;
  context: RhViolationContext;
};