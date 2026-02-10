"use client";

import * as React from "react";
import { toast } from "sonner";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DayTypeSelect } from "@/components/planning/DayTypeSelect";
import { QualifiedTrancheSelect } from "@/features/planning-agent/components/QualifiedTrancheSelect";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { bulkUpsertTeamPlanningDays } from "@/services/team-planning.service";
import type {
  TeamBulkFailedItem,
  TeamPlanningBulkItem,
} from "@/types/teamPlanning";

export function TeamBulkEditSheet(props: {
  open: boolean;
  onClose: () => void;

  teamId: number;
  items: TeamPlanningBulkItem[];

  onApplied?: () => void | Promise<void>;
}) {
  const { open, onClose, teamId, items, onApplied } = props;

  const formId = "team-bulk-edit-form";

  const [dayType, setDayType] = React.useState<string>("working");
  const [trancheId, setTrancheId] = React.useState<number | null>(null);
  const [description, setDescription] = React.useState<string>("");

  const [submitting, setSubmitting] = React.useState(false);
  const [failed, setFailed] = React.useState<TeamBulkFailedItem[]>([]);

  const isWorking = dayType === "working";

  const agentCount = items.length;
  const cellCount = React.useMemo(
    () => items.reduce((sum, it) => sum + it.day_dates.length, 0),
    [items],
  );

  React.useEffect(() => {
    if (!open) return;
    setFailed([]);
  }, [open]);

  React.useEffect(() => {
    if (dayType !== "working") setTrancheId(null);
  }, [dayType]);

  const canSubmit =
    teamId > 0 &&
    agentCount > 0 &&
    cellCount > 0 &&
    dayType.length > 0 &&
    (!isWorking || trancheId !== null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setFailed([]);

    try {
      const res = await bulkUpsertTeamPlanningDays(teamId, {
        items,
        day_type: dayType,
        description: description.trim() === "" ? null : description.trim(),
        tranche_id: isWorking ? trancheId : null,
      });

      const updatedCount = res.updated?.length ?? 0;
      const failedCount = res.failed?.length ?? 0;

      if (failedCount > 0) {
        setFailed(res.failed);

        if (updatedCount > 0) {
          const sample = res.failed
            .slice(0, 2)
            .map((f) => `${f.agent_id}/${f.day_date}: ${f.code}`)
            .join(" • ");

          toast.warning("Mises à jour partielles", {
            description: `${updatedCount} appliquées — ${failedCount} échec(s)${
              sample ? ` (${sample})` : ""
            }`,
          });
        } else {
          toast.error("Aucune mise à jour appliquée", {
            description: res.failed[0]?.message ?? `${failedCount} échec(s)`,
          });
        }

        // on reste ouvert pour afficher les erreurs
        return;
      }

      toast.success("Mises à jour appliquées", {
        description: `${updatedCount} mise(s) à jour`,
      });

      await onApplied?.();
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erreur inconnue";
      toast.error("Erreur lors de l’application", { description: msg });

      setFailed([{ agent_id: 0, day_date: "", code: "unknown", message: msg }]);
    } finally {
      setSubmitting(false);
    }
  }

  // pour proposer une tranche : on prend un exemple (1er agent + 1ère date)
  const sampleAgentId = items[0]?.agent_id ?? 0;
  const sampleDateISO = items[0]?.day_dates[0] ?? null;

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={(v) => (!v ? onClose() : null)}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      title={
        <>
          Éditer {agentCount} agent{agentCount > 1 ? "s" : ""} • {cellCount} cellule
          {cellCount > 1 ? "s" : ""}
        </>
      }
      description={
        <span className="text-xs text-muted-foreground">
          Les modifications seront appliquées à toutes les cellules sélectionnées.
        </span>
      }
      bodyClassName="p-4"
      footer={
        <>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={submitting}
          >
            Annuler
          </Button>
          <Button type="submit" form={formId} disabled={!canSubmit || submitting}>
            {submitting ? "Application…" : "Appliquer"}
          </Button>
        </>
      }
    >
      <form id={formId} onSubmit={onSubmit} className="space-y-6">
        <DayTypeSelect value={dayType} onValueChange={setDayType} disabled={submitting} />

        {isWorking ? (
          <QualifiedTrancheSelect
            agentId={sampleAgentId}
            value={trancheId}
            onChange={setTrancheId}
            disabled={submitting}
            dateISO={sampleDateISO}
            label="Tranche"
          />
        ) : null}

        <div className="space-y-2">
          <Label>Commentaire (optionnel)</Label>
          <Textarea
            placeholder="Ajouter un commentaire…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={submitting}
          />
        </div>

        {failed.length ? (
          <div className="rounded-lg border p-3">
            <div className="text-sm font-medium">
              Certaines mises à jour ont échoué
            </div>
            <div className="mt-2 space-y-1 text-sm text-muted-foreground">
              {failed.slice(0, 10).map((f, i) => (
                <div key={i}>
                  <span className="font-medium">
                    Agent {f.agent_id} • {f.day_date || "—"} :
                  </span>{" "}
                  {f.message} <span className="text-xs">({f.code})</span>
                </div>
              ))}
              {failed.length > 10 ? (
                <div className="text-xs">+{failed.length - 10} autres…</div>
              ) : null}
            </div>
          </div>
        ) : null}
      </form>
    </PlanningSheetShell>
  );
}
