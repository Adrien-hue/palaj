"use client";

import type { AgentDetails } from "@/types";
import { AdminDetailsCard } from "@/components/admin/AdminDetailsCard";
import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

export function AgentRegimeCard({ agent }: { agent: AgentDetails }) {
  return (
    <AdminDetailsCard title="Régime">
      {agent.regime ? (
        <div>
          <AdminDetailsRow label="Nom" value={agent.regime.nom} />
          <AdminDetailsRow label="Description" value={agent.regime.desc || "—"} />
        </div>
      ) : (
        <div className="text-sm text-zinc-600">Aucun régime.</div>
      )}
    </AdminDetailsCard>
  );
}
