"use client";

import * as React from "react";
import { X } from "lucide-react";

import type { Agent } from "@/types";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import type { Draft } from "@/features/planning-poste/utils/poste-day-sheet/draft";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";
import { timeLabelHHMM } from "@/utils/time.format";
import { cn } from "@/lib/utils";

import { AgentSelect } from "@/features/agents/components/AgentSelect";
import { AgentSelectStatusById } from "@/features/agents/components/agentSelect.types";

type CoverageVariant = "secondary" | "success" | "warning";

export function PosteDayTranchesSection({
  day,
  isEditing,
  draft,
  setDraft,

  availableAgents,
  agentById,

  isAgentsLoading,
  isStatusLoading,
  isSaving,
  isDeleting,

  statusByAgentId,
}: {
  day: PosteDayVm;

  isEditing: boolean;
  draft: Draft;
  setDraft: React.Dispatch<React.SetStateAction<Draft>>;

  availableAgents: Agent[];
  agentById: Map<number, Agent>;

  isAgentsLoading: boolean;
  isStatusLoading: boolean;
  isSaving: boolean;
  isDeleting: boolean;

  statusByAgentId: AgentSelectStatusById | undefined;
}) {
  const removeAgent = React.useCallback(
    (trancheId: number, agentId: number) => {
      setDraft((d) => ({
        ...d,
        [trancheId]: (d[trancheId] ?? []).filter((x) => x !== agentId),
      }));
    },
    [setDraft],
  );

  const addAgent = React.useCallback(
    (trancheId: number, agentId: number) => {
      setDraft((d) => ({
        ...d,
        [trancheId]: Array.from(new Set([...(d[trancheId] ?? []), agentId])),
      }));
    },
    [setDraft],
  );

  return (
    <DrawerSection title="Tranches">
      {day.tranches.length === 0 ? (
        <EmptyBox>Aucune tranche</EmptyBox>
      ) : (
        <div className="space-y-2">
          {day.tranches.map((t) => {
            const trancheId = t.tranche.id;
            const trancheColor = t.tranche.color ?? null;

            const agentIds = isEditing
              ? (draft[trancheId] ?? [])
              : t.agents.map((a) => a.id);

            const assigned = agentIds.length;
            const required = t.coverage?.required ?? 0;
            const isConfigured = t.coverage?.isConfigured ?? false;

            const missing =
              isConfigured && required > 0 ? Math.max(0, required - assigned) : 0;

            const isUnderCovered = isConfigured && required > 0 && missing > 0;

            const trancheCardClass = isUnderCovered
              ? "border-amber-500/40 bg-amber-500/5"
              : "border-border bg-background";

            const trancheBadgeVariant: CoverageVariant = !isConfigured
              ? "secondary"
              : required === 0
                ? "secondary"
                : missing === 0
                  ? "success"
                  : "warning";

            const trancheBadgeText = !isConfigured
              ? "Non configuré"
              : required === 0
                ? "0 requis"
                : `${assigned}/${required}`;

            const trancheTooltip = !isConfigured
              ? "Couverture non configurée pour cette tranche."
              : required === 0
                ? "Aucun besoin configuré pour cette tranche."
                : missing === 0
                  ? `Couverture OK (${assigned}/${required}).`
                  : `Sous-couverture : ${assigned}/${required} (manque ${missing}).`;

            const selectableAgents =
              isEditing && !(isAgentsLoading || isStatusLoading)
                ? availableAgents.filter((a) => !agentIds.includes(a.id))
                : [];

            const selectDisabled =
              isSaving ||
              isDeleting ||
              !isEditing ||
              isAgentsLoading ||
              isStatusLoading ||
              selectableAgents.length === 0;

            const selectPlaceholder = isAgentsLoading
              ? "Chargement des agents…"
              : isStatusLoading
                ? "Chargement des statuts…"
                : selectableAgents.length
                  ? "Sélectionner un agent…"
                  : "Aucun agent disponible";

            return (
              <div
                key={trancheId}
                className={cn(
                  "relative overflow-hidden rounded border p-3 transition-colors",
                  trancheCardClass,
                )}
              >
                {trancheColor ? (
                  <div
                    className="absolute left-0 top-0 h-1 w-full"
                    style={{ backgroundColor: trancheColor }}
                    aria-hidden
                  />
                ) : null}

                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 shrink-0 rounded-full border border-border"
                        style={trancheColor ? { backgroundColor: trancheColor } : undefined}
                        aria-hidden
                      />
                      <div className="truncate text-sm font-semibold">
                        {t.tranche.nom}
                      </div>
                    </div>

                    <div className="text-xs text-muted-foreground tabular-nums">
                      {timeLabelHHMM(t.tranche.heure_debut)}–
                      {timeLabelHHMM(t.tranche.heure_fin)}
                    </div>
                  </div>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge
                        variant={trancheBadgeVariant}
                        className="shrink-0 tabular-nums"
                        tabIndex={0}
                        aria-label={trancheTooltip}
                      >
                        {trancheBadgeText}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>{trancheTooltip}</TooltipContent>
                  </Tooltip>
                </div>

                {/* Agents */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {agentIds.length === 0 ? (
                    <span className="text-sm text-muted-foreground">
                      Aucun agent affecté.
                    </span>
                  ) : (
                    agentIds.map((id) => {
                      const a = agentById.get(id);
                      const label = a ? `${a.prenom} ${a.nom}` : `#${id}`;

                      return (
                        <Badge
                          key={id}
                          variant="outline"
                          className="rounded-full px-2 py-1 text-xs font-normal"
                        >
                          <span className="mr-1">{label}</span>

                          {isEditing ? (
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5 rounded-full"
                              onClick={() => removeAgent(trancheId, id)}
                              aria-label={`Retirer ${label}`}
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          ) : null}
                        </Badge>
                      );
                    })
                  )}
                </div>

                {/* Add agent */}
                {isEditing ? (
                  <div className="mt-3 space-y-2">
                    <AgentSelect
                      onChange={(id) => {
                        if (id == null) return;
                        addAgent(trancheId, id);
                      }}
                      agents={selectableAgents}
                      statusByAgentId={statusByAgentId}
                      disabled={selectDisabled}
                      label="Ajouter un agent"
                      placeholder={selectPlaceholder}
                      emptyLabel={
                        isAgentsLoading || isStatusLoading
                          ? "Chargement…"
                          : "Aucun agent correspondant"
                      }
                    />
                  </div>
                ) : null}

                {isEditing && isAgentsLoading ? (
                  <div className="mt-2 text-xs text-muted-foreground">
                    Chargement des agents qualifiés…
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </DrawerSection>
  );
}
