import { AgentPicker } from "@/components/agents/AgentPicker";
import { listAgents } from "@/services";
import type { ListParams } from "@/types";

export default async function PlanningAgentsIndexPage() {
  const params: ListParams = {page: 1, page_size: 200};
  const data = await listAgents(params);
  
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-[color:var(--app-text)]">
          Planning par agent
        </h1>
        <p className="max-w-2xl text-[color:var(--app-muted)]">
          Sélectionne un agent pour consulter et modifier son planning.
        </p>
      </header>

      <AgentPicker agents={data.items} />
    </div>
  );
}
