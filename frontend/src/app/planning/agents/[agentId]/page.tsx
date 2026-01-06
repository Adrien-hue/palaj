import { notFound } from "next/navigation";

import { getAgentPlanning } from "@/services/planning.service";
import { listPostes } from "@/services/postes.service";

import { buildPlanningVm } from "@/features/planning/vm/planning.vm.builder";
import {
  monthAnchorISO,
  monthGridRangeFrom,
} from "@/features/planning/utils/month.utils";

import { MonthNavigator } from "@/features/planning/components/MonthNavigator";
import { MonthlyPlanningGrid } from "@/features/planning/components/MonthlyPlanningGrid";

type PageProps = {
  params: Promise<{ agentId: string }>;
  searchParams: Promise<{ date?: string }>;
};

export default async function AgentPlanningPage({
  params,
  searchParams,
}: PageProps) {
  const [{ agentId: rawId }, { date }] = await Promise.all([
    params,
    searchParams,
  ]);

  const agentId = Number(rawId);
  if (!Number.isFinite(agentId)) notFound();

  // Anchor du mois: YYYY-MM-01
  const anchor = monthAnchorISO(date ?? new Date().toISOString().slice(0, 10));
  const range = monthGridRangeFrom(anchor);

  const [planningDto, postesList] = await Promise.all([
    getAgentPlanning(agentId, {
      startDate: range.start,
      endDate: range.end,
    }),
    listPostes(),
  ]);

  const planning = buildPlanningVm(planningDto);

  const posteNameById = new Map<number, string>(
    postesList.items.map((p) => [p.id, p.nom])
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-6xl p-6">
        <MonthNavigator />
        <div className="mb-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
          <div className="text-2xl font-semibold text-foreground">
            {planning.agent.prenom} {planning.agent.nom}
          </div>
          <div className="text-sm text-muted-foreground">Planning mensuel</div>
        </div>

        <MonthlyPlanningGrid
          anchorMonth={anchor}
          planning={planning}
          posteNameById={posteNameById}
        />
      </div>
    </div>
  );
}
