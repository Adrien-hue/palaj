"use client";

import * as React from "react";

import type { Poste } from "@/types/postes";
import type { Agent, PostePlanningDayPutBody } from "@/types";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import { Badge } from "@/components/ui/badge";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { EmptyBox } from "@/components/planning/DrawerSection";

import { PosteCoverageBadge } from "../PosteCoverageBadge";
import { useAgentDayStatusesBatch } from "@/features/planning-poste/hooks/useAgentDayStatusesBatch";
import { useRhPosteDay } from "@/features/rh-validation/hooks/useRhPosteDay";

import {
  Draft,
  buildBodyFromDraft,
  buildDraftFromDay,
  isSameDraft,
} from "@/features/planning-poste/utils/poste-day-sheet/draft";

import { PosteDaySheetActions } from "./PosteDaySheetActions";
import { PosteDayTranchesSection } from "./PosteDayTranchesSection";
import { PosteDayRhSection } from "./PosteDayRhSection";

/* helpers */
function formatDateFRLong(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(d);
}

export function PosteDaySheet({
  open,
  onClose,
  day,
  poste,
  availableAgents,
  isAgentsLoading = false,
  onSaveDay,
  onDeleteDay,
  isSaving = false,
  isDeleting = false,

  rhProfile,
  rangeStart,
  rangeEnd,
}: {
  open: boolean;
  onClose: () => void;
  day: PosteDayVm | null;
  poste: Poste;

  availableAgents: Agent[];
  isAgentsLoading?: boolean;

  onSaveDay: (args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    body: PostePlanningDayPutBody;
  }) => Promise<unknown>;
  onDeleteDay: (dayDate: string) => Promise<unknown>;

  isSaving?: boolean;
  isDeleting?: boolean;

  rhProfile: "fast" | "full";
  rangeStart: string;
  rangeEnd: string;
}) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [draft, setDraft] = React.useState<Draft>({});
  const [initialDraft, setInitialDraft] = React.useState<Draft>({});

  React.useEffect(() => {
    if (!open || !day) return;

    const d = buildDraftFromDay(day);
    setDraft(d);
    setInitialDraft(d);
    setIsEditing(false);
  }, [open, day?.day_date]);

  const isDirty = day ? !isSameDraft(draft, initialDraft) : false;

  const agentById = React.useMemo(() => {
    const m = new Map<number, Agent>();
    availableAgents.forEach((a) => m.set(a.id, a));
    return m;
  }, [availableAgents]);

  const agentLabel = React.useCallback(
    (id: number) => {
      const a = agentById.get(id);
      if (!a) return `Agent #${id} (non chargé)`;
      return `${a.prenom} ${a.nom}`;
    },
    [agentById],
  );

  // statuses : fetch uniquement en édition, une seule fois, sur tous les agents qualifiés
  const statusAgentIds = React.useMemo(() => {
    if (!isEditing) return [];
    return availableAgents.map((a) => a.id);
  }, [isEditing, availableAgents]);

  const statuses = useAgentDayStatusesBatch({
    dayDate: isEditing ? (day?.day_date ?? null) : null,
    agentIds: statusAgentIds,
  });

  const isStatusLoading = statuses.isLoading;

  const rhDay = useRhPosteDay({
    posteId: poste.id,
    day: open ? (day?.day_date ?? null) : null,
    startDate: rangeStart,
    endDate: rangeEnd,
    profile: rhProfile,
    includeInfo: false,
    enabled: open && !!day,
  });

  if (!open) return null;

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      bodyClassName="p-4"
      title={
        <span className="flex items-center gap-2">
          <span className="truncate">
            {day ? formatDateFRLong(day.day_date) : "Jour"}
          </span>
          {day ? <PosteCoverageBadge day={day} /> : <Badge variant="secondary">—</Badge>}
        </span>
      }
      description={<span>{poste.nom}</span>}
    >
      {!day ? (
        <EmptyBox>Aucun jour sélectionné.</EmptyBox>
      ) : (
        <div className="space-y-4">
          <PosteDaySheetActions
            isEditing={isEditing}
            isDirty={isDirty}
            isSaving={isSaving}
            isDeleting={isDeleting}
            dayLabel={formatDateFRLong(day.day_date)}
            onStartEdit={() => setIsEditing(true)}
            onCancelEdit={() => {
              setDraft(initialDraft);
              setIsEditing(false);
            }}
            onSave={async () => {
              await onSaveDay({
                dayDate: day.day_date,
                day_type: day.day_type,
                description: day.description ?? null,
                body: buildBodyFromDraft(draft),
              });

              await Promise.all([statuses.refresh(), rhDay.mutate()]);

              setInitialDraft(draft);
              setIsEditing(false);
            }}
            onDeleteConfirmed={async () => {
              await onDeleteDay(day.day_date);
              
              await Promise.all([statuses.refresh(), rhDay.mutate()]);

              onClose();
            }}
          />

          <PosteDayRhSection
            rhDay={{
              data: rhDay.data,
              isLoading: rhDay.isLoading,
              isValidating: rhDay.isValidating,
              error: rhDay.error,
            }}
            agentLabel={agentLabel}
            onRefresh={() => rhDay.mutate()}
          />

          <PosteDayTranchesSection
            day={day}
            isEditing={isEditing}
            draft={draft}
            setDraft={setDraft}
            availableAgents={availableAgents}
            agentById={agentById}
            isAgentsLoading={isAgentsLoading}
            isStatusLoading={isStatusLoading}
            isSaving={isSaving}
            isDeleting={isDeleting}
            statusByAgentId={statuses.statusByAgentId}
          />
        </div>
      )}
    </PlanningSheetShell>
  );
}
