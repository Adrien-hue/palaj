import type { RegimeBase, Regime, UpdateRegimeBody } from "@/types";

/**
 * Build a minimal PATCH payload by comparing a draft with the initial regime.
 * - Trims strings
 * - Converts empty description to null (so user can clear it)
 * - Keeps nullable numbers as-is (null clears the value)
 */
export function buildRegimePatch(initial: Regime, draft: RegimeBase): UpdateRegimeBody {
  const patch: UpdateRegimeBody = {};

  // Strings
  const nextNom = draft.nom.trim();
  if (nextNom !== initial.nom) patch.nom = nextNom;

  const nextDesc = (draft.desc ?? "").trim();
  const normalizedDesc = nextDesc.length === 0 ? null : nextDesc;
  const initialDesc = (initial.desc ?? "").trim();
  const normalizedInitialDesc = initialDesc.length === 0 ? null : initialDesc;
  if (normalizedDesc !== normalizedInitialDesc) patch.desc = normalizedDesc;

  // Nullable numbers helpers
  const setIfChanged = <
    K extends keyof RegimeBase & keyof UpdateRegimeBody
  >(
    key: K
  ) => {
    const next = (draft[key] ?? null) as UpdateRegimeBody[K];
    const prev = (initial[key] ?? null) as UpdateRegimeBody[K];

    if (next !== prev) {
      patch[key] = next;
    }
  };


  setIfChanged("min_rp_annuels");
  setIfChanged("min_rp_dimanches");
  setIfChanged("min_rpsd");
  setIfChanged("min_rp_2plus");
  setIfChanged("min_rp_semestre");
  setIfChanged("avg_service_minutes");
  setIfChanged("avg_tolerance_minutes");

  return patch;
}
