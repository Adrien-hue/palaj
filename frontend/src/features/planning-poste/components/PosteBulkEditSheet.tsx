"use client";

import * as React from "react";

import type { Poste } from "@/types/postes";
import type { Agent, PostePlanningDayPutBody } from "@/types";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

import { AgentSelect } from "@/features/agents/components/AgentSelect";
import { timeLabelHHMM } from "@/utils/time.format";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

type Draft = Record<number, number[]>; // trancheId -> agentIds

function buildBodyFromDraft(draft: Draft): PostePlanningDayPutBody {
  return {
    tranches: Object.entries(draft).map(([trancheId, agentIds]) => ({
      tranche_id: Number(trancheId),
      agent_ids: agentIds,
    })),
    cleanup_empty_agent_days: true,
  };
}

function uniqSorted(ids: number[]) {
  return Array.from(new Set(ids)).sort((a, b) => a - b);
}

export function PosteBulkEditSheet(props: {
  open: boolean;
  onClose: () => void;

  posteId: number;
  poste: Poste;

  /** dates ISO YYYY-MM-DD */
  selectedDates: string[];

  /** agents déjà filtrés (idéalement qualifiés poste) */
  availableAgents: Agent[];
  isAgentsLoading?: boolean;

  /** Optionnel: pour afficher les infos des tranches */
  tranches?: Array<{
    id: number;
    nom: string;
    heure_debut: string;
    heure_fin: string;
    color?: string | null;
  }>;

  /** callback d'application (réutilise ton action existante) */
  onSaveDay: (args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    body: PostePlanningDayPutBody;
  }) => Promise<unknown>;

  /** utile pour reset sélection côté client */
  onApplied?: () => void;

  /** si tu veux pré-remplir le draft depuis un jour sélectionné */
  seedFromDay?: PosteDayVm | null;
}) {
  const {
    open,
    onClose,
    poste,
    selectedDates,
    availableAgents,
    isAgentsLoading = false,
    onSaveDay,
    onApplied,
    tranches,
    seedFromDay,
  } = props;

  const formId = "poste-bulk-edit-form";
  const selectedCount = selectedDates.length;

  const [submitting, setSubmitting] = React.useState(false);
  const [errors, setErrors] = React.useState<
    Array<{ day_date: string; message: string }>
  >([]);

  const [draft, setDraft] = React.useState<Draft>({});

  // seed: si tu veux pré-remplir depuis un jour (optionnel)
  React.useEffect(() => {
    if (!open) return;
    setErrors([]);

    if (seedFromDay?.tranches?.length) {
      const next: Draft = {};
      for (const t of seedFromDay.tranches) {
        next[t.tranche.id] = t.agents.map((a) => a.id);
      }
      setDraft(next);
    } else {
      // V1: draft vide au départ (utilisateur ajoute à la main)
      setDraft({});
    }
  }, [open, seedFromDay?.day_date]); // eslint-disable-line react-hooks/exhaustive-deps

  const agentById = React.useMemo(() => {
    const m = new Map<number, Agent>();
    for (const a of availableAgents) m.set(a.id, a);
    return m;
  }, [availableAgents]);

  const trancheById = React.useMemo(() => {
    const m = new Map<number, NonNullable<typeof tranches>[number]>();
    for (const t of tranches ?? []) m.set(t.id, t);
    return m;
  }, [tranches]);

  const trancheIds = React.useMemo(() => {
    // si on a la liste des tranches => ordre stable
    if (tranches?.length) return tranches.map((t) => t.id);

    // sinon => on utilise celles du draft
    return Object.keys(draft)
      .map((k) => Number(k))
      .filter((n) => Number.isFinite(n))
      .sort((a, b) => a - b);
  }, [tranches, draft]);

  const removeAgent = (trancheId: number, agentId: number) => {
    setDraft((d) => ({
      ...d,
      [trancheId]: (d[trancheId] ?? []).filter((x) => x !== agentId),
    }));
  };

  const addAgent = (trancheId: number, agentId: number) => {
    setDraft((d) => ({
      ...d,
      [trancheId]: uniqSorted([...(d[trancheId] ?? []), agentId]),
    }));
  };

  const canSubmit =
    selectedCount > 0 &&
    !isAgentsLoading &&
    // draft peut être vide mais dans ce cas ça "clean" tout => on préfère bloquer V1
    Object.keys(draft).length > 0;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setErrors([]);

    const body = buildBodyFromDraft(draft);

    const failed: Array<{ day_date: string; message: string }> = [];

    try {
      // V1: appliquer séquentiellement (plus simple à lire/debug)
      // Optimisation plus tard: Promise.allSettled avec limite de concurrence
      for (const dayDate of selectedDates) {
        try {
          await onSaveDay({
            dayDate,
            day_type: "working",
            description: null,
            body,
          });
        } catch (err) {
          failed.push({
            day_date: dayDate,
            message: err instanceof Error ? err.message : "Erreur inconnue",
          });
        }
      }

      if (failed.length) {
        setErrors(failed);
        return;
      }

      onApplied?.();
      onClose();
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
          Les affectations seront appliquées à tous les jours sélectionnés pour{" "}
          <span className="font-medium">{poste.nom}</span>.
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
        {/* V1 info */}
        <div className="rounded-xl border bg-card p-3 text-sm text-muted-foreground">
          Sélectionnez des agents par tranche. Cette configuration sera copiée
          sur <span className="font-medium">{selectedCount}</span>{" "}
          {selectedCount > 1 ? "jours" : "jour"}.
        </div>

        <DrawerSection
          title="Affectations"
          subtitle="Définissez le contenu cible par tranche."
          className="border-border bg-card"
        >
          {trancheIds.length === 0 ? (
            <EmptyBox>
              Aucune tranche à éditer. (Astuce : passe `tranches` au composant
              pour afficher la liste complète.)
            </EmptyBox>
          ) : (
            <div className="space-y-2">
              {trancheIds.map((trancheId) => {
                const t = trancheById.get(trancheId);
                const trancheColor = t?.color ?? null;
                const agentIds = draft[trancheId] ?? [];

                const selectableAgents = isAgentsLoading
                  ? []
                  : availableAgents.filter((a) => !agentIds.includes(a.id));

                const cardClass = "border-border bg-background";

                return (
                  <div
                    key={trancheId}
                    className={cn(
                      "relative overflow-hidden rounded border p-3 transition-colors",
                      cardClass
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
                            style={
                              trancheColor
                                ? { backgroundColor: trancheColor }
                                : undefined
                            }
                            aria-hidden
                          />
                          <div className="truncate text-sm font-semibold">
                            {t?.nom ?? `Tranche #${trancheId}`}
                          </div>
                        </div>

                        {t ? (
                          <div className="text-xs text-muted-foreground tabular-nums">
                            {timeLabelHHMM(t.heure_debut)}–{timeLabelHHMM(t.heure_fin)}
                          </div>
                        ) : null}
                      </div>

                      <Badge variant="secondary" className="shrink-0 tabular-nums">
                        {agentIds.length} agent{agentIds.length > 1 ? "s" : ""}
                      </Badge>
                    </div>

                    {/* Agents sélectionnés */}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {agentIds.length === 0 ? (
                        <span className="text-sm text-muted-foreground">
                          Aucun agent sélectionné.
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

                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                className="h-5 w-5 rounded-full"
                                onClick={() => removeAgent(trancheId, id)}
                                aria-label={`Retirer ${label}`}
                                disabled={submitting}
                              >
                                <X className="h-3.5 w-3.5" />
                              </Button>
                            </Badge>
                          );
                        })
                      )}
                    </div>

                    {/* Add agent */}
                    <div className="mt-3 space-y-2">
                      <Label className="text-xs">Ajouter un agent</Label>

                      <AgentSelect
                        onChange={(id) => {
                          if (id == null) return;
                          addAgent(trancheId, id);
                        }}
                        agents={selectableAgents}
                        disabled={
                          submitting ||
                          isAgentsLoading ||
                          selectableAgents.length === 0
                        }
                        placeholder={
                          selectableAgents.length
                            ? "Sélectionner un agent…"
                            : "Aucun agent disponible"
                        }
                        emptyLabel="Aucun agent correspondant"
                      />

                      {isAgentsLoading ? (
                        <div className="text-xs text-muted-foreground">
                          Chargement des agents…
                        </div>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </DrawerSection>

        {errors.length ? (
          <div className="rounded-lg border p-3">
            <div className="text-sm font-medium">
              Certaines mises à jour ont échoué
            </div>

            <div className="mt-2 space-y-1 text-sm text-muted-foreground">
              {errors.slice(0, 8).map((e, i) => (
                <div key={i}>
                  {e.day_date ? (
                    <span className="font-medium">{e.day_date} :</span>
                  ) : null}{" "}
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
