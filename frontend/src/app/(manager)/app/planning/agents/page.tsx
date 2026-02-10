import { listAgents } from "@/services/agents.service";
import { listPostes } from "@/services/postes.service";
import { monthAnchorISO } from "@/features/planning-common/utils/month.utils";
import { AgentPlanningClient } from "@/features/planning-agent/components/AgentPlanningClient";

type PageProps = {
  searchParams: Promise<{ date?: string; anchor?: string }>;
};

export default async function AgentsPlanningPage({ searchParams }: PageProps) {
  const sp = await searchParams;

  const [agentsList] = await Promise.all([listAgents()]);

  const todayISO = new Date().toISOString().slice(0, 10);
  const initialAnchor = monthAnchorISO(sp.anchor ?? sp.date ?? todayISO);

  return (
    <AgentPlanningClient
      initialAgentId={null}
      initialAnchor={initialAnchor}
      agents={agentsList.items}
    />
  );
}
