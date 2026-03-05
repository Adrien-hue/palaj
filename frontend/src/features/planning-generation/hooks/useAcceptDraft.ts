"use client";

import useSWRMutation from "swr/mutation";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

export type DraftDecisionStatus = "accepted" | "rejected";

export type DraftDecisionResponse = {
  draft_id?: number;
  status?: DraftDecisionStatus | string;
  [key: string]: unknown;
};

type AcceptDraftKey = readonly ["planningGeneration", "acceptDraft", number];

function keyOf(draftId: number | null): AcceptDraftKey | null {
  if (!draftId) return null;
  return ["planningGeneration", "acceptDraft", draftId];
}

async function postAccept([, , id]: AcceptDraftKey) {
  return apiFetch<DraftDecisionResponse>(backendPath(`/planning/drafts/${id}/accept`), {
    method: "POST",
  });
}

export function useAcceptDraft(draftId: number | null) {
  return useSWRMutation(keyOf(draftId), postAccept);
}
