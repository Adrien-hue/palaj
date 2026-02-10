"use client";

import * as React from "react";
import type { AgentPlanningKey } from "@/features/planning-agent/hooks/agentPlanning.key";

import { useAgentPlanning } from "@/features/planning-agent/hooks/useAgentPlanning";
import { useAgentPlanningEdit } from "@/features/planning-agent/hooks/useAgentPlanningEdit";

import { buildPlanningVm } from "../vm/agentPlanning.vm.builder";
import type { AgentDayVm } from "../vm/agentPlanning.vm";

import { AgentDaySheetView, type AgentDaySheetSavePayload } from "./AgentDaySheetView";

export function AgentDaySheet({
  open,
  onClose,
  agentId,
  dayDateISO,
  planningKey,
}: {
  open: boolean;
  onClose: () => void;
  agentId: number;
  dayDateISO: string | null;
  planningKey: AgentPlanningKey | null;
}) {
  const enabled = open && !!dayDateISO;

  const { data, isLoading, isValidating, error, mutate } = useAgentPlanning(
    enabled
      ? { agentId, startDate: dayDateISO!, endDate: dayDateISO! }
      : { agentId, startDate: "1970-01-01", endDate: "1970-01-01" }
  );

  const planningVm = React.useMemo(() => {
    if (!data || !enabled) return null;
    return buildPlanningVm(data);
  }, [data, enabled]);

  const day: AgentDayVm | null = React.useMemo(() => {
    if (!planningVm || !dayDateISO) return null;
    return planningVm.days[0] ?? null;
  }, [planningVm, dayDateISO]);

  const { saveDay, removeDay } = useAgentPlanningEdit(agentId, planningKey);

  const [isSaving, setIsSaving] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [actionError, setActionError] = React.useState<string | null>(null);

  async function handleSave(payload: AgentDaySheetSavePayload) {
    try {
      setActionError(null);
      setIsSaving(true);

      await saveDay({
        dayDate: payload.dayDate,
        day_type: payload.day_type,
        description: payload.description,
        tranche_id: payload.tranche_id,
      });

      if (mutate) await mutate();
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Erreur lors de l’enregistrement"
      );
      throw e;
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(dayDate: string) {
    try {
      setActionError(null);
      setIsDeleting(true);

      await removeDay(dayDate);

      if (mutate) await mutate();
      onClose();
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Erreur lors de la suppression"
      );
      throw e;
    } finally {
      setIsDeleting(false);
    }
  }

  const busy = isSaving || isDeleting;

  return (
    <AgentDaySheetView
      open={open}
      onClose={onClose}
      day={day}
      agentId={agentId}
      onSave={handleSave}
      onDelete={handleDelete}
      loading={isLoading}
      validating={isValidating}
      loadError={error?.message ?? null}
      actionError={actionError}
      busy={busy}
    />
  );
}
