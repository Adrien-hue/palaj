"use client";

import useSWRMutation from "swr/mutation";

import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { DraftDecisionResponse } from "./useAcceptDraft";

type RejectDraftKey = readonly ["planningGeneration", "rejectDraft", number];

function keyOf(draftId: number | null): RejectDraftKey | null {
  if (!draftId) return null;
  return ["planningGeneration", "rejectDraft", draftId];
}

async function postReject([, , id]: RejectDraftKey) {
  return apiFetch<DraftDecisionResponse>(backendPath(`/planning/drafts/${id}/reject`), {
    method: "POST",
  });
}

export function useRejectDraft(draftId: number | null) {
  return useSWRMutation(keyOf(draftId), postReject);
}
