import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import type { RhDaySummary } from "@/types";

import { computeTrancheCoverageCounts } from "./posteCoverageTranches";

export type PosteDayTone = "none" | "info" | "warning" | "danger";

export function computePosteDayTone(args: {
  day: PosteDayVm;
  rh?: RhDaySummary;
  isOutsideMonth?: boolean;
  isOutsideRange?: boolean;
}): PosteDayTone {
  const { day, rh, isOutsideMonth, isOutsideRange } = args;

  // Outside => le frame gère déjà l’opacité
  if (isOutsideMonth || isOutsideRange) return "none";

  // 1) RH blockers = danger (priorité max)
  if ((rh?.agents_with_blockers_count ?? 0) > 0) return "danger";

  // 2) Couverture (au sens "tranches") => warning si au moins une tranche manquante
  const trancheCov = computeTrancheCoverageCounts(day);
  if (trancheCov.isConfigured && trancheCov.total > 0 && trancheCov.missing > 0) {
    return "warning";
  }

  // 3) RH issues / risk => info (ou warning si vous voulez plus agressif)
  if ((rh?.agents_with_issues_count ?? 0) > 0) return "info";
  if (rh?.risk === "high") return "info";
  if (rh?.risk === "medium") return "info";

  return "none";
}
