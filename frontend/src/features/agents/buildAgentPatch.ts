import type { Agent } from "@/types";

export type AgentFormSubmitValues = {
  nom: string;
  prenom: string;
  code_personnel: string;
  regime_id: number | null;
};

export function buildAgentPatch(initial: Agent, next: AgentFormSubmitValues) {
  const patch: Record<string, unknown> = {};

  if (next.nom !== initial.nom) patch.nom = next.nom;
  if (next.prenom !== initial.prenom) patch.prenom = next.prenom;

  const initialCode = (initial as any).code_personnel ?? "";
  if (next.code_personnel !== initialCode) patch.code_personnel = next.code_personnel;

  const initialRegime = (initial as any).regime_id ?? null;
  if (next.regime_id !== initialRegime) patch.regime_id = next.regime_id;

  return patch;
}