"use client";

import type { AgentDetails } from "@/types";
import { AdminStatBadge } from "@/components/admin/AdminStatBadge";
import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

export function AgentHeaderCard({ agent }: { agent: AgentDetails }) {
  return (
    <div className="rounded-2xl bg-zinc-50 p-4 ring-1 ring-zinc-200">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-base font-semibold text-zinc-900">
            {agent.nom} {agent.prenom}
          </div>
          <div className="mt-1 text-xs text-zinc-600">ID: {agent.id}</div>
        </div>
        <AdminStatBadge active={agent.actif} />
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        <AdminDetailsRow label="Code personnel" value={agent.code_personnel || "—"} />
        <AdminDetailsRow
          label="Régime"
          value={agent.regime ? agent.regime.nom : agent.regime_id ?? "—"}
        />
      </div>
    </div>
  );
}
