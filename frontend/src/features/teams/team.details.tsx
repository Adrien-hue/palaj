"use client";

import type { Team } from "@/types";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

function formatDateTime(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

export default function TeamDetails({ team }: { team: Team }) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="bg-muted/40">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{team.name}</CardTitle>
          <div className="mt-1 text-xs text-muted-foreground">ID: {team.id}</div>
        </CardHeader>
      </Card>

      {/* Description */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-foreground">{team.description || "—"}</div>
        </CardContent>
      </Card>

      {/* Infos */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Informations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          <AdminDetailsRow label="Créée le" value={formatDateTime(team.created_at)} />
        </CardContent>
      </Card>
    </div>
  );
}
