import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

export type TrancheCoverageCounts = {
  total: number;
  covered: number;
  missing: number;
  isConfigured: boolean;
};

export function computeTrancheCoverageCounts(day: PosteDayVm): TrancheCoverageCounts {
  const configured = day.tranches.filter(
    (t) => t.coverage?.isConfigured && (t.coverage.required ?? 0) > 0
  );

  const total = configured.length;
  const covered = configured.filter((t) => (t.coverage?.assigned ?? 0) > 0).length;

  return {
    total,
    covered,
    missing: Math.max(0, total - covered),
    isConfigured: total > 0,
  };
}

export function trancheCoverageVariant(c: TrancheCoverageCounts): "secondary" | "success" | "warning" {
  if (!c.isConfigured || c.total === 0) return "secondary";
  return c.missing === 0 ? "success" : "warning";
}

export function trancheCoverageLabel(c: TrancheCoverageCounts) {
  if (!c.isConfigured) return "Couverture non configurée (tranches)";
  if (c.total === 0) return "Aucun besoin configuré (tranches)";
  if (c.missing === 0) return "Toutes les tranches sont couvertes";
  return "Certaines tranches ne sont pas couvertes";
}

export function trancheCoverageRatio(c: TrancheCoverageCounts) {
  if (!c.isConfigured) return "—";
  return `${c.covered}/${c.total}`;
}
