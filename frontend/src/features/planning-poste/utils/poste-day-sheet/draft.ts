import type { PostePlanningDayPutBody } from "@/types";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

export type Draft = Record<number, number[]>; // trancheId -> agentIds

export function buildDraftFromDay(day: PosteDayVm): Draft {
  const d: Draft = {};
  for (const t of day.tranches ?? []) {
    d[t.tranche.id] = t.agents.map((a) => a.id);
  }
  return d;
}

export function buildBodyFromDraft(draft: Draft): PostePlanningDayPutBody {
  return {
    tranches: Object.entries(draft).map(([trancheId, agentIds]) => ({
      tranche_id: Number(trancheId),
      agent_ids: agentIds,
    })),
    cleanup_empty_agent_days: true,
  };
}

export function isSameDraft(a: Draft, b: Draft) {
  const ak = Object.keys(a);
  const bk = Object.keys(b);
  if (ak.length !== bk.length) return false;

  for (const k of ak) {
    const av = [...(a[+k] ?? [])].sort();
    const bv = [...(b[+k] ?? [])].sort();
    if (av.length !== bv.length) return false;
    for (let i = 0; i < av.length; i++) {
      if (av[i] !== bv[i]) return false;
    }
  }
  return true;
}
