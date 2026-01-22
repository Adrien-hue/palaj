import { notFound } from "next/navigation";

import { getAgentPlanning } from "@/services/planning.service";
import { listPostes } from "@/services/postes.service";

import { buildPlanningVm } from "@/features/planning-agent/vm/agentPlanning.vm.builder";
import {
  monthAnchorISO,
  monthGridRangeFrom,
} from "@/features/planning-common/utils/month.utils";

import { PlanningPageHeader, PlanningMonthControls } from "@/features/planning-common";
import { AgentMonthlyPlanningGrid } from "@/features/planning-agent/components/AgentMonthlyPlanningGrid";

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
    getAgentPlanning(agentId, { startDate: range.start, endDate: range.end }),
    listPostes(),
  ]);

  const planning = buildPlanningVm(planningDto);
  const agent = planning.agent;

  const agentName = `${agent.prenom} ${agent.nom}`;

  const posteNameById = new Map<number, string>(
    postesList.items.map((p) => [p.id, p.nom])
  );

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        crumbs={[
          { label: "Planning", href: "/app" },
          { label: "Par agent", href: "/app/planning/agents" },
          { label: agentName },
        ]}
        backHref="/app/planning/agents"
        title={agentName}
        subtitle="Planning mensuel"
        controls={<PlanningMonthControls navMode="replace" />}
      />

      <AgentMonthlyPlanningGrid
        anchorMonth={anchor}
        planning={planning}
        posteNameById={posteNameById}
      />
    </div>
  );
}
