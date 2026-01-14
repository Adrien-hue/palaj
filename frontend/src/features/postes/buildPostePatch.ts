import type { Poste } from "@/types";

export function buildPostePatch(initial: Poste, next: { nom: string }) {
  const patch: Record<string, unknown> = {};
  if (next.nom !== initial.nom) patch.nom = next.nom;
  return patch;
}
