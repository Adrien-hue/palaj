import { notFound } from "next/navigation";

import { getPostePlanning } from "@/services/planning.service";
import type { PostePlanning } from "@/types/postePlanning";

import { buildPostePlanningVm } from "@/features/planning-poste/vm/postePlanning.vm.builder";

import {
  monthAnchorISO,
  monthGridRangeFrom,
} from "@/features/planning-common/utils/month.utils";

import { PlanningPageHeader } from "@/features/planning-common";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";

import { PosteMonthlyPlanningGrid } from "@/features/planning-poste/components/PosteMonthlyPlanningGrid";
import { formatDateFR } from "@/utils/date.format";

type PageProps = {
  params: Promise<{ posteId: string }>;
  searchParams: Promise<{
    anchor?: string;
    start?: string;
    end?: string;

    date?: string;
  }>;
};

export default async function PostePlanningPage({ params, searchParams }: PageProps) {
  const [{ posteId: rawId }, sp] = await Promise.all([params, searchParams]);

  const posteId = Number(rawId);
  if (!Number.isFinite(posteId)) notFound();

  const todayISO = new Date().toISOString().slice(0, 10);

  const isRange = !!(sp.start && sp.end);

  const anchorMonth = isRange
    ? monthAnchorISO(sp.start!)
    : monthAnchorISO(sp.anchor ?? sp.date ?? todayISO);

  const range = isRange
    ? { start: sp.start!, end: sp.end! }
    : monthGridRangeFrom(anchorMonth);

  const subtitle = isRange
    ? `Couverture du ${formatDateFR(range.start)} au ${formatDateFR(range.end)}`
    : "Couverture mensuelle";

  const dto: PostePlanning = await getPostePlanning(posteId, {
    startDate: range.start,
    endDate: range.end,
  });

  const planning = buildPostePlanningVm(dto);
  const poste = planning.poste;

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        titleSlot={<div className="text-2xl font-semibold">{poste.nom}</div>}
        subtitle={subtitle}
        rightSlot={<PlanningPeriodControls navMode="replace" />}
      />

      <PosteMonthlyPlanningGrid anchorMonth={anchorMonth} planning={planning} />
    </div>
  );
}
