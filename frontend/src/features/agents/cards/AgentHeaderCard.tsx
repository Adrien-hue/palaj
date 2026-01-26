"use client";

import type { AgentDetails } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { AdminStatBadge } from "@/components/admin/AdminStatBadge";
import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

export function AgentHeaderCard({ agent }: { agent: AgentDetails }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="truncate text-base font-semibold">
              {agent.nom} {agent.prenom}
            </div>
            <div className="mt-1 text-xs text-muted-foreground">ID: {agent.id}</div>
          </div>

          <AdminStatBadge active={agent.actif} />
        </div>
      </CardHeader>

      <CardContent className="pt-0">
          <AdminDetailsRow label="Code personnel" value={agent.code_personnel || "—"} />
          <AdminDetailsRow
            label="Régime"
            value={agent.regime ? agent.regime.nom : agent.regime_id ?? "—"}
            className="sm:border-b-0"
          />
      </CardContent>
    </Card>
  );
}
