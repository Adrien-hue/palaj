import type { TeamBase, Team, PatchTeamBody } from "@/types";

/**
 * Build a minimal PATCH payload by comparing a draft with the initial team.
 * - Trims strings
 * - Converts empty description to null (so user can clear it)
 */
export function buildTeamPatch(
  initial: Team,
  draft: TeamBase
): PatchTeamBody {
  const patch: PatchTeamBody = {};

  // name (string, required)
  const nextName = draft.name.trim();
  if (nextName && nextName !== initial.name) patch.name = nextName;


  // description (string | null)
  const nextDesc = (draft.description ?? "").trim();
  const normalizedNextDesc = nextDesc.length === 0 ? null : nextDesc;

  const initialDesc = (initial.description ?? "").trim();
  const normalizedInitialDesc =
    initialDesc.length === 0 ? null : initialDesc;

  if (normalizedNextDesc !== normalizedInitialDesc) {
    patch.description = normalizedNextDesc;
  }

  return patch;
}
