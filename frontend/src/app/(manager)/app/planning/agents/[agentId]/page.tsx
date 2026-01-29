import { notFound } from "next/navigation";

import { getAgentPlanning } from "@/services/planning.service";
import { listPostes } from "@/services/postes.service";

import { buildPlanningVm } from "@/features/planning-agent/vm/agentPlanning.vm.builder";
import {
  monthAnchorISO,
  monthGridRangeFrom,
} from "@/features/planning-common/utils/month.utils";

import { PlanningPageHeader } from "@/features/planning-common";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";

import { AgentMonthlyPlanningGrid } from "@/features/planning-agent/components/AgentMonthlyPlanningGrid";
import { formatDateFR } from "@/utils/date.format";

type PageProps = {
  params: Promise<{ agentId: string }>;
  searchParams: Promise<{
    // ✅ nouveau : période
    anchor?: string; // YYYY-MM-DD (on attend surtout YYYY-MM-01)
    start?: string; // YYYY-MM-DD
    end?: string; // YYYY-MM-DD

    // ✅ legacy
    date?: string; // YYYY-MM-DD
  }>;
};

export default async function AgentPlanningPage({
  params,
  searchParams,
}: PageProps) {
  const [{ agentId: rawId }, sp] = await Promise.all([params, searchParams]);

  const agentId = Number(rawId);
  if (!Number.isFinite(agentId)) notFound();

  const todayISO = new Date().toISOString().slice(0, 10);

  // ---------------------------------------
  // ✅ Période (range prioritaire)
  // ---------------------------------------
  const isRange = !!(sp.start && sp.end);

  const anchorMonth = isRange
    ? monthAnchorISO(sp.start!) // on accroche l’affichage du grid sur le mois du start
    : monthAnchorISO(sp.anchor ?? sp.date ?? todayISO);

  const range = isRange
    ? { start: sp.start!, end: sp.end! }
    : monthGridRangeFrom(anchorMonth);

  const subtitle = isRange
    ? `Planning du ${formatDateFR(range.start)} au ${formatDateFR(range.end)}`
    : "Planning mensuel";

  const [planningDto, postesList] = await Promise.all([
    getAgentPlanning(agentId, { startDate: range.start, endDate: range.end }),
    listPostes(),
  ]);

  const planning = buildPlanningVm(planningDto);
  const agent = planning.agent;
  const agentName = `${agent.prenom} ${agent.nom}`;

  const posteNameById = new Map<number, string>(
    postesList.items.map((p) => [p.id, p.nom]),
  );

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        titleSlot={<div className="text-2xl font-semibold">{agentName}</div>}
        subtitle={subtitle}
        rightSlot={<PlanningPeriodControls navMode="replace" />}
      />

      <AgentMonthlyPlanningGrid
        anchorMonth={anchorMonth}
        planning={planning}
        posteNameById={posteNameById}
      />
    </div>
  );
}
