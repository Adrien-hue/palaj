import type { RhDaySummary, RhPosteSummaryResponse } from "@/types";

export type RhPosteSummaryVm = {
  posteId: number;
  range: { startISO: string; endISO: string };
  profile: string;
  eligibleAgentsCount: number;
  byDate: Record<string, RhDaySummary>;
};

export function buildRhPosteSummaryVm(dto: RhPosteSummaryResponse): RhPosteSummaryVm {
  const byDate: Record<string, RhDaySummary> = {};

  for (const day of dto.days) {
    // defensive: day.date attendu YYYY-MM-DD
    if (day?.date) byDate[day.date] = day;
  }

  return {
    posteId: dto.poste_id,
    range: { startISO: dto.date_debut, endISO: dto.date_fin },
    profile: dto.profile,
    eligibleAgentsCount: dto.eligible_agents_count,
    byDate,
  };
}
