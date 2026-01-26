"use client";

import type { PosteDetail } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function StatPill({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border bg-muted/30 px-3 py-2">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="text-sm font-semibold tabular-nums">{value}</div>
    </div>
  );
}

export function PosteHeaderCard({
  poste,
  tranchesCount,
  qualificationsCount,
}: {
  poste: PosteDetail;
  tranchesCount: number;
  qualificationsCount: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{poste.nom}</CardTitle>
        <div className="mt-1 text-xs text-muted-foreground">ID: {poste.id}</div>
      </CardHeader>

      <CardContent>
        <div className="grid gap-2 sm:grid-cols-2">
          <StatPill label="Tranches" value={tranchesCount} />
          <StatPill label="Qualifications" value={qualificationsCount} />
        </div>
      </CardContent>
    </Card>
  );
}
