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
      : // fallback pour éviter un fetch non désiré si ton hook ne supporte pas "enabled"
        { agentId, startDate: "1970-01-01", endDate: "1970-01-01" },
  );

  const planningVm = React.useMemo(() => {
    if (!data || !enabled) return null;
    return buildPlanningVm(data);
  }, [data, enabled]);

  const day: AgentDayVm | null = React.useMemo(() => {
    if (!planningVm || !dayDateISO) return null;
    // range 1 jour => day[0]
    return planningVm.days[0] ?? null;
  }, [planningVm, dayDateISO]);

  const { saveDay, removeDay } = useAgentPlanningEdit(agentId, planningKey);

  async function handleSave(payload: AgentDaySheetSavePayload) {
    await saveDay({
      dayDate: payload.dayDate,
      day_type: payload.day_type,
      description: payload.description,
      tranche_id: payload.tranche_id,
    });

    if (mutate) await mutate();
  }

  async function handleDelete(dayDate: string) {
    await removeDay(dayDate);

    if (mutate) await mutate();
    onClose();
  }

  return (
    <AgentDaySheetView
      open={open}
      onClose={onClose}
      day={day}
      agentId={agentId}
      onSave={handleSave}
      onDelete={handleDelete}
    />
  );
}
