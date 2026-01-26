"use client";

import type { RegimeDetail } from "@/types";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

function show(v?: number | null) {
  return v == null ? "—" : v;
}

export default function RegimeDetails({ regime }: { regime: RegimeDetail }) {
  const agents = regime.agents ?? [];
  const preview = agents.slice(0, 10);

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="bg-muted/40">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{regime.nom}</CardTitle>
          <div className="mt-1 text-xs text-muted-foreground">ID: {regime.id}</div>
        </CardHeader>
      </Card>

      {/* Description */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-foreground">{regime.desc || "—"}</div>
        </CardContent>
      </Card>

      {/* Règles */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Règles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          <AdminDetailsRow label="Min RP annuels" value={show(regime.min_rp_annuels)} />
          <AdminDetailsRow label="Min RP dimanches" value={show(regime.min_rp_dimanches)} />
          <AdminDetailsRow label="Min RPSD" value={show(regime.min_rpsd)} />
          <AdminDetailsRow label="Min RP 2+" value={show(regime.min_rp_2plus)} />
          <AdminDetailsRow label="Min RP semestre" value={show(regime.min_rp_semestre)} />
        </CardContent>
      </Card>

      {/* Moyennes */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Moyennes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          <AdminDetailsRow
            label="Avg service (min)"
            value={show(regime.avg_service_minutes)}
          />
          <AdminDetailsRow
            label="Avg tolerance (min)"
            value={show(regime.avg_tolerance_minutes)}
          />
        </CardContent>
      </Card>

      {/* Agents */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-sm">Agents</CardTitle>
            <div className="text-xs text-muted-foreground">{agents.length}</div>
          </div>
        </CardHeader>

        <CardContent className="space-y-2">
          {agents.length === 0 ? (
            <div className="text-sm text-muted-foreground">Aucun agent associé.</div>
          ) : (
            <>
              <div className="space-y-2">
                {preview.map((a) => (
                  <div
                    key={a.id}
                    className="flex items-center justify-between gap-3 rounded-lg border bg-muted/40 px-3 py-2"
                  >
                    <div className="min-w-0 truncate text-sm">
                      {a.nom} {a.prenom}
                    </div>
                    <div className="shrink-0 text-xs text-muted-foreground">#{a.id}</div>
                  </div>
                ))}
              </div>

              {agents.length > preview.length ? (
                <div className="text-xs text-muted-foreground">
                  +{agents.length - preview.length} autres…
                </div>
              ) : null}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
