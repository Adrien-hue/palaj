import { notFound } from "next/navigation";

import { getPostePlanning } from "@/services/planning.service";
import type { PostePlanning } from "@/types/postePlanning";

import { buildPostePlanningVm } from "@/features/planning-poste/vm/postePlanning.vm.builder";

import {
  monthAnchorISO,
  monthGridRangeFrom,
} from "@/features/planning-common/utils/month.utils";

import { PlanningPageHeader, PlanningMonthControls } from "@/features/planning-common"; 
import { PosteMonthlyPlanningGrid } from "@/features/planning-poste/components/PosteMonthlyPlanningGrid";

type PageProps = {
  params: Promise<{ posteId: string }>;
  searchParams: Promise<{ date?: string }>;
};

export default async function PostePlanningPage({ params, searchParams }: PageProps) {
  const [{ posteId: rawId }, { date }] = await Promise.all([params, searchParams]);

  const posteId = Number(rawId);
  if (!Number.isFinite(posteId)) notFound();

  const anchor = monthAnchorISO(date ?? new Date().toISOString().slice(0, 10));
  const range = monthGridRangeFrom(anchor);

  const dto: PostePlanning = await getPostePlanning(posteId, {
    startDate: range.start,
    endDate: range.end,
  });

  const planning = buildPostePlanningVm(dto);
  const poste = planning.poste;

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        crumbs={[
          { label: "Planning", href: "/app" },
          { label: "Par poste", href: "/app/planning/postes" },
          { label: poste.nom },
        ]}
        backHref="/app/planning/postes"
        title={poste.nom}
        subtitle="Couverture mensuelle"
        controls={<PlanningMonthControls navMode="replace" />}
      />
      <PosteMonthlyPlanningGrid anchorMonth={anchor} planning={planning} />
    </div>
  );
}
