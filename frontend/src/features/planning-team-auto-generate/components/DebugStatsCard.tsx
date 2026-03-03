"use client";

import * as React from "react";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

import type { PlanningGenerateJobStatusResponse } from "../hooks/useTeamPlanningGenerate";

function prettyValue(value: unknown) {
  if (value == null) return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "string" && value.trim() === "") return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

export function DebugStatsCard({ data }: { data?: PlanningGenerateJobStatusResponse }) {
  const [copySuccess, setCopySuccess] = React.useState(false);

  const stats = data?.result_stats;
  const summary = [
    { label: "solver_status", value: data?.solver_status },
    {
      label: "normalized_solver_status",
      value: (stats?.normalized_solver_status as unknown) ?? null,
    },
    { label: "coverage_ratio", value: stats?.coverage_ratio },
    { label: "solve_time_seconds", value: stats?.solve_time_seconds },
    { label: "soft_violations", value: stats?.soft_violations },
    { label: "num_assignments", value: stats?.num_assignments },
    { label: "is_timeout", value: (stats?.is_timeout as unknown) ?? null },
    { label: "objective_value", value: (stats?.objective_value as unknown) ?? null },
    { label: "score", value: stats?.score },
  ];

  const detailsPayload = React.useMemo(
    () => ({
      status: data?.status,
      job_id: data?.job_id,
      draft_id: data?.draft_id,
      progress: data?.progress,
      solver_status: data?.solver_status,
      result_stats: data?.result_stats,
      error: data?.error,
    }),
    [data],
  );

  const onCopy = React.useCallback(async () => {
    if (!data || typeof navigator === "undefined" || !navigator.clipboard) return;
    await navigator.clipboard.writeText(JSON.stringify(detailsPayload, null, 2));
    setCopySuccess(true);
    window.setTimeout(() => setCopySuccess(false), 1200);
  }, [data, detailsPayload]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Résumé debug</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!data ? (
          <p className="text-sm text-muted-foreground">Aucun statut chargé.</p>
        ) : (
          <>
            <dl className="grid grid-cols-1 gap-2 md:grid-cols-3">
              {summary.map((item) => (
                <div key={item.label} className="rounded-md border p-2">
                  <dt className="text-xs text-muted-foreground">{item.label}</dt>
                  <dd className="text-sm font-medium">{prettyValue(item.value)}</dd>
                </div>
              ))}
            </dl>

            <Accordion type="single" collapsible>
              <AccordionItem value="details">
                <AccordionTrigger>Afficher détails</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <div className="flex items-center justify-end">
                    <Button type="button" variant="outline" size="sm" onClick={onCopy}>
                      {copySuccess ? "Copié" : "Copier JSON"}
                    </Button>
                  </div>
                  <ScrollArea className="h-64 rounded-md border bg-muted/30 p-2">
                    <pre className="font-mono text-xs">{JSON.stringify(detailsPayload, null, 2)}</pre>
                  </ScrollArea>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </>
        )}
      </CardContent>
    </Card>
  );
}
