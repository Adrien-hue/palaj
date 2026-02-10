"use client";

import * as React from "react";
import { mutate } from "swr";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DayTypeSelect } from "@/components/planning/DayTypeSelect";
import { QualifiedTrancheSelect } from "@/features/planning-agent/components/QualifiedTrancheSelect";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import type { AgentPlanningKey } from "@/features/planning-agent/hooks/agentPlanning.key";
import { bulkUpsertAgentPlanningDays } from "@/services/agent-planning.service";

export function AgentBulkEditSheet(props: {
  open: boolean;
  onClose: () => void;

  agentId: number;
  planningKey: AgentPlanningKey | null;

  selectedDates: string[];

  onApplied?: () => void;
}) {
  const {
    open,
    onClose,
    agentId,
    planningKey,
    selectedDates,
    onApplied,
  } = props;

  const formId = "agent-bulk-edit-form";

  const [dayType, setDayType] = React.useState<string>("working");
  const [trancheId, setTrancheId] = React.useState<number | null>(null);
  const [description, setDescription] = React.useState<string>("");

  const [submitting, setSubmitting] = React.useState(false);
  const [errors, setErrors] = React.useState<
    Array<{ day_date: string; message: string }>
  >([]);

  const isWorking = dayType === "working";
  const selectedCount = selectedDates.length;

  React.useEffect(() => {
    if (!open) return;
    setErrors([]);
  }, [open]);

  React.useEffect(() => {
    if (dayType !== "working") setTrancheId(null);
  }, [dayType]);

  const canSubmit =
    selectedCount > 0 && dayType.length > 0 && (!isWorking || trancheId !== null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setErrors([]);

    try {
      const res = await bulkUpsertAgentPlanningDays(agentId, {
        day_dates: selectedDates,
        day_type: dayType,
        description: description.trim() === "" ? null : description.trim(),
        tranche_id: isWorking ? trancheId : null,
      });

      if (planningKey) await mutate(planningKey);

      if (res.failed?.length) {
        setErrors(res.failed.map((f) => ({ day_date: f.day_date, message: f.message })));
        return;
      }

      onApplied?.();
      onClose();
    } catch (err) {
      setErrors([
        { day_date: "", message: err instanceof Error ? err.message : "Erreur inconnue" },
      ]);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={(v) => (!v ? onClose() : null)}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      title={
        <>
          Éditer {selectedCount} {selectedCount > 1 ? "jours" : "jour"}
        </>
      }
      description={
        <span className="text-xs text-muted-foreground">
          Les modifications seront appliquées à tous les jours sélectionnés.
        </span>
      }
      bodyClassName="p-4"
      footer={
        <>
          <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
            Annuler
          </Button>
          <Button
            type="submit"
            form={formId}
            disabled={!canSubmit || submitting}
          >
            {submitting ? "Application…" : "Appliquer"}
          </Button>
        </>
      }
    >
      <form id={formId} onSubmit={onSubmit} className="space-y-6">
        <DayTypeSelect value={dayType} onValueChange={setDayType} />

        {isWorking ? (
          <QualifiedTrancheSelect
            agentId={agentId}
            value={trancheId}
            onChange={setTrancheId}
            disabled={submitting}
            dateISO={null}
            label="Tranche"
          />
        ) : null}

        <div className="space-y-2">
          <Label>Commentaire (optionnel)</Label>
          <Textarea
            placeholder="Ajouter un commentaire…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {errors.length ? (
          <div className="rounded-lg border p-3">
            <div className="text-sm font-medium">Certaines mises à jour ont échoué</div>
            <div className="mt-2 space-y-1 text-sm text-muted-foreground">
              {errors.slice(0, 8).map((e, i) => (
                <div key={i}>
                  {e.day_date ? <span className="font-medium">{e.day_date} :</span> : null}{" "}
                  {e.message}
                </div>
              ))}
              {errors.length > 8 ? (
                <div className="text-xs">+{errors.length - 8} autres…</div>
              ) : null}
            </div>
          </div>
        ) : null}
      </form>
    </PlanningSheetShell>
  );
}
