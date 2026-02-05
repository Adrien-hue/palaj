"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";

import type { Poste } from "@/types/postes";
import type { Agent, PostePlanningDayPutBody } from "@/types";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";
import { timeLabelHHMM } from "@/utils/time.format";

/* -------------------------------- helpers -------------------------------- */

function formatDateFRLong(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(d);
}

type CoverageVariant = "secondary" | "success" | "warning";

function dayCoverageVariant(day: PosteDayVm | null): CoverageVariant {
  if (!day) return "secondary";
  const { required, missing, isConfigured } = day.coverage;
  if (!isConfigured || required === 0) return "secondary";
  return missing === 0 ? "success" : "warning";
}

function dayCoverageRatio(day: PosteDayVm | null) {
  if (!day || !day.coverage.isConfigured) return "—";
  const { required, assigned } = day.coverage;
  return required > 0 ? `${assigned}/${required}` : "0/0";
}

/* -------------------------------- draft -------------------------------- */

type Draft = Record<number, number[]>; // trancheId -> agentIds

function buildDraftFromDay(day: PosteDayVm): Draft {
  const d: Draft = {};
  for (const t of day.tranches ?? []) {
    d[t.tranche.id] = t.agents.map((a) => a.id);
  }
  return d;
}

function buildBodyFromDraft(draft: Draft): PostePlanningDayPutBody {
  return {
    tranches: Object.entries(draft).map(([trancheId, agentIds]) => ({
      tranche_id: Number(trancheId),
      agent_ids: agentIds,
    })),
    cleanup_empty_agent_days: true,
  };
}

function isSameDraft(a: Draft, b: Draft) {
  const ak = Object.keys(a);
  const bk = Object.keys(b);
  if (ak.length !== bk.length) return false;

  for (const k of ak) {
    const av = [...(a[+k] ?? [])].sort();
    const bv = [...(b[+k] ?? [])].sort();
    if (av.length !== bv.length) return false;
    for (let i = 0; i < av.length; i++) {
      if (av[i] !== bv[i]) return false;
    }
  }
  return true;
}

/* -------------------------------- component -------------------------------- */

export function PosteDaySheet({
  open,
  onClose,
  day,
  poste,
  availableAgents,
  onSaveDay,
  onDeleteDay,
  isSaving = false,
  isDeleting = false,
}: {
  open: boolean;
  onClose: () => void;
  day: PosteDayVm | null;
  poste: Poste;

  availableAgents: Agent[];
  onSaveDay: (args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    body: PostePlanningDayPutBody;
  }) => Promise<unknown>;
  onDeleteDay: (dayDate: string) => Promise<unknown>;

  isSaving?: boolean;
  isDeleting?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState<Draft>({});
  const [initialDraft, setInitialDraft] = useState<Draft>({});

  useEffect(() => {
    if (!open || !day) return;

    const d = buildDraftFromDay(day);
    setDraft(d);
    setInitialDraft(d);
    setIsEditing(false);
  }, [open, day?.day_date]);

  const isDirty = day ? !isSameDraft(draft, initialDraft) : false;

  const agentById = useMemo(() => {
    const m = new Map<number, Agent>();
    availableAgents.forEach((a) => m.set(a.id, a));
    return m;
  }, [availableAgents]);

  const removeAgent = (trancheId: number, agentId: number) => {
    setDraft((d) => ({
      ...d,
      [trancheId]: (d[trancheId] ?? []).filter((x) => x !== agentId),
    }));
  };

  const addAgent = (trancheId: number, agentId: number) => {
    setDraft((d) => ({
      ...d,
      [trancheId]: Array.from(new Set([...(d[trancheId] ?? []), agentId])),
    }));
  };

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
          <Badge variant={dayCoverageVariant(day)}>
            {dayCoverageRatio(day)}
          </Badge>
        </span>
      }
      description={<span>{poste.nom}</span>}
    >
      {!day ? (
        <EmptyBox>Aucun jour sélectionné.</EmptyBox>
      ) : (
        <div className="space-y-4">
          {/* Actions */}
          <div className="flex justify-between gap-2">
            {isEditing ? (
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setDraft(initialDraft);
                    setIsEditing(false);
                  }}
                  disabled={isSaving || isDeleting}
                >
                  Annuler
                </Button>

                <Button
                  disabled={!isDirty || isSaving || isDeleting}
                  onClick={async () => {
                    await onSaveDay({
                      dayDate: day.day_date,
                      day_type: day.day_type,
                      description: day.description ?? null,
                      body: buildBodyFromDraft(draft),
                    });
                    setInitialDraft(draft);
                    setIsEditing(false);
                  }}
                >
                  {isSaving ? "Enregistrement…" : "Enregistrer"}
                </Button>
              </div>
            ) : (
              <Button
                onClick={() => setIsEditing(true)}
                disabled={isSaving || isDeleting}
              >
                Modifier
              </Button>
            )}

            <Button
              variant="destructive"
              disabled={isDeleting || isSaving}
              onClick={async () => {
                await onDeleteDay(day.day_date);
                onClose();
              }}
            >
              {isDeleting ? "Suppression…" : "Supprimer"}
            </Button>
          </div>

          <DrawerSection title="Tranches">
            {day.tranches.length === 0 ? (
              <EmptyBox>Aucune tranche</EmptyBox>
            ) : (
              <div className="space-y-2">
                {day.tranches.map((t) => {
                  const trancheId = t.tranche.id;
                  const agentIds = isEditing
                    ? draft[trancheId] ?? []
                    : t.agents.map((a) => a.id);

                  const selectableAgents = availableAgents.filter(
                    (a) => !agentIds.includes(a.id)
                  );

                  const selectId = `add-agent-${day.day_date}-${trancheId}`;

                  return (
                    <div key={trancheId} className="rounded-xl border p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold">
                            {t.tranche.nom}
                          </div>
                          <div className="text-xs text-muted-foreground tabular-nums">
                            {timeLabelHHMM(t.tranche.heure_debut)}–
                            {timeLabelHHMM(t.tranche.heure_fin)}
                          </div>
                        </div>
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

                      {/* Add agent (shadcn Select) */}
                      {isEditing ? (
                        <div className="mt-3 space-y-2">
                          <Label htmlFor={selectId} className="text-xs">
                            Ajouter un agent
                          </Label>

                          <Select
                            onValueChange={(v) => {
                              const id = Number(v);
                              if (!Number.isFinite(id)) return;
                              addAgent(trancheId, id);
                            }}
                            disabled={
                              isSaving || isDeleting || selectableAgents.length === 0
                            }
                          >
                            <SelectTrigger id={selectId} className="w-full">
                              <SelectValue
                                placeholder={
                                  selectableAgents.length
                                    ? "Sélectionner un agent…"
                                    : "Aucun agent disponible"
                                }
                              />
                            </SelectTrigger>

                            <SelectContent>
                              {selectableAgents.map((a) => (
                                <SelectItem key={a.id} value={String(a.id)}>
                                  {a.prenom} {a.nom}
                                  {a.code_personnel ? ` (${a.code_personnel})` : ""}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}
          </DrawerSection>
        </div>
      )}
    </PlanningSheetShell>
  );
}
