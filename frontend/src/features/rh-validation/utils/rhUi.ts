import type { RhRisk } from "@/types";

export function rhRiskLabel(r: RhRisk) {
  if (r === "high") return "Élevé";
  if (r === "medium") return "Moyen";
  if (r === "low") return "Faible";
  return "Aucun";
}

export function rhRiskRank(r: RhRisk) {
  return r === "high" ? 0 : r === "medium" ? 1 : r === "low" ? 2 : 3;
}

export function rhDayCardTone(args: { blockers: number; issues: number; risk: RhRisk }) {
  const { blockers, issues, risk } = args;
  if (blockers > 0) return "danger" as const;
  if (issues > 0) return "warning" as const;
  if (risk === "high" || risk === "medium") return "info" as const;
  return "none" as const;
}

export function rhDayCardClass(args: { blockers: number; issues: number; risk: RhRisk }) {
  const tone = rhDayCardTone(args);
  if (tone === "danger") return "border-destructive/35 bg-destructive/5";
  if (tone === "warning") return "border-amber-500/30 bg-amber-500/5";
  if (tone === "info") return "border-muted-foreground/20 bg-muted/0";
  return "";
}
