import type { Tranche } from "@/types";
import type { PosteCoverageDto } from "@/types/posteCoverage";

export type PosteCoverageConfigVm = {
  posteId: number;
  trancheById: Record<number, Tranche>;
  requiredByWeekday: Record<number, Record<number, number>>; // 0..6 (lundi..dimanche)
};

export function buildPosteCoverageConfigVm(dto: PosteCoverageDto): PosteCoverageConfigVm {
  const trancheById: Record<number, Tranche> = {};
  for (const t of dto.tranches) trancheById[t.id] = t;

  const requiredByWeekday: Record<number, Record<number, number>> = {};
  for (const r of dto.requirements) {
    (requiredByWeekday[r.weekday] ??= {});
    requiredByWeekday[r.weekday][r.tranche_id] = r.required_count;
  }

  return {
    posteId: dto.poste_id,
    trancheById,
    requiredByWeekday,
  };
}
