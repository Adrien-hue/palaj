"use client";

import { useMemo } from "react";

import type { Poste } from "@/types/postes";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import { Badge } from "@/components/ui/badge";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { timeLabelHHMM } from "@/utils/time.format";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";

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

  if (!isConfigured) return "secondary";
  if (required === 0) return "secondary";
  return missing === 0 ? "success" : "warning";
}

function dayCoverageLabel(day: PosteDayVm | null) {
  if (!day) return "Couverture";
  const { required, missing, isConfigured } = day.coverage;

  if (!isConfigured) return "Couverture non configurée";
  if (required === 0) return "Aucun besoin configuré";
  if (missing === 0) return "Couverture complète";
  return "Couverture incomplète";
}

function dayCoverageRatio(day: PosteDayVm | null) {
  if (!day) return "—";
  const { required, assigned, isConfigured } = day.coverage;

  if (!isConfigured) return "—";
  return required > 0 ? `${assigned}/${required}` : "0/0";
}

function sortTranchesForCoverage<
  T extends {
    tranche: { heure_debut: string; nom: string };
    agents: any[];
    coverage?: {
      required: number;
      assigned: number;
      delta: number;
      isConfigured: boolean;
    };
  }
>(tranches: T[]) {
  return [...tranches].sort((a, b) => {
    // 1) Priorité: sous-couverture (missing > 0) en haut
    const aReq = a.coverage?.required ?? 0;
    const bReq = b.coverage?.required ?? 0;

    const aAssigned = a.coverage?.assigned ?? (a.agents?.length ?? 0);
    const bAssigned = b.coverage?.assigned ?? (b.agents?.length ?? 0);

    const aMissing = Math.max(0, aReq - aAssigned);
    const bMissing = Math.max(0, bReq - bAssigned);

    const aIsConfigured = a.coverage?.isConfigured ?? false;
    const bIsConfigured = b.coverage?.isConfigured ?? false;

    // Configuré + manque => d'abord
    const aPriority = aIsConfigured && aReq > 0 && aMissing > 0;
    const bPriority = bIsConfigured && bReq > 0 && bMissing > 0;
    if (aPriority !== bPriority) return aPriority ? -1 : 1;

    // Puis non configuré en bas (optionnel mais souvent plus lisible)
    if (aIsConfigured !== bIsConfigured) return aIsConfigured ? -1 : 1;

    // 2) Ensuite: manque le plus important en premier
    if (aMissing !== bMissing) return bMissing - aMissing;

    // 3) Ensuite: heure de début
    const ha = (a.tranche.heure_debut ?? "").slice(0, 8);
    const hb = (b.tranche.heure_debut ?? "").slice(0, 8);
    if (ha !== hb) return ha.localeCompare(hb);

    // 4) Ensuite: nom
    return (a.tranche.nom ?? "").localeCompare(b.tranche.nom ?? "", "fr");
  });
}

export function PosteDaySheet({
  open,
  onOpenChange,
  day,
  poste,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  day: PosteDayVm | null;
  poste: Poste;
}) {
  const ratio = dayCoverageRatio(day);
  const label = dayCoverageLabel(day);

  const coverageText = !day
    ? "Couverture"
    : !day.coverage.isConfigured
      ? "Couverture non configurée"
      : day.coverage.required === 0
        ? "Aucun besoin configuré"
        : `${label} • ${ratio} • manque ${day.coverage.missing}`;

  const sortedTranches = useMemo(
    () => (day?.tranches?.length ? sortTranchesForCoverage(day.tranches) : []),
    [day?.tranches]
  );

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={onOpenChange}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      rootClassName="bg-background"
      bodyClassName="p-4"
      title={
        <span className="flex min-w-0 items-center gap-2">
          <span className="truncate">
            {day ? formatDateFRLong(day.day_date) : "Jour"}
          </span>

          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant={dayCoverageVariant(day)}
                className="shrink-0 tabular-nums"
                tabIndex={0}
                aria-label={coverageText}
                title={label}
              >
                {ratio}
              </Badge>
            </TooltipTrigger>

            <TooltipContent className="max-w-[280px]">
              {!day ? (
                <div className="text-xs text-muted-foreground">
                  Aucun jour sélectionné.
                </div>
              ) : !day.coverage.isConfigured ? (
                <div className="space-y-1 text-xs">
                  <div className="font-medium">Couverture</div>
                  <div className="text-muted-foreground">
                    Aucune règle de couverture n’est configurée pour ce jour.
                  </div>
                </div>
              ) : day.coverage.required === 0 ? (
                <div className="space-y-1 text-xs">
                  <div className="font-medium">Couverture</div>
                  <div className="text-muted-foreground">
                    Aucun besoin configuré.
                  </div>
                </div>
              ) : (
                <div className="space-y-1 text-xs">
                  <div className="font-medium">Couverture</div>
                  <div className="flex items-center justify-between gap-2 text-muted-foreground">
                    <span>Besoin</span>
                    <span className="tabular-nums">{day.coverage.required}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 text-muted-foreground">
                    <span>Affectés</span>
                    <span className="tabular-nums">{day.coverage.assigned}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 text-muted-foreground">
                    <span>Manque</span>
                    <span className="tabular-nums">{day.coverage.missing}</span>
                  </div>
                </div>
              )}
            </TooltipContent>
          </Tooltip>
        </span>
      }
      description={<span className="truncate">{poste.nom} • Détail des tranches</span>}
    >
      <div className="space-y-4">
        {!day ? (
          <EmptyBox>Aucun jour sélectionné.</EmptyBox>
        ) : (
          <>
            {day.description ? (
              <div className="rounded-xl border border-border bg-card p-3 text-sm text-muted-foreground">
                {day.description}
              </div>
            ) : null}

            {day.is_off_shift ? (
              <div className="rounded-xl border border-border bg-muted/40 p-3 text-sm text-foreground">
                Poste indiqué comme “OFF” ce jour.
              </div>
            ) : null}

            <DrawerSection
              variant="surface"
              title="Tranches"
              subtitle="Détail des affectations par tranche."
              className="border-border bg-card"
            >
              {sortedTranches.length ? (
                <div className="space-y-2">
                  {sortedTranches.map((t) => {
                    const assigned = t.agents.length;

                    const required = t.coverage?.required ?? 0;
                    const isConfigured = t.coverage?.isConfigured ?? false;

                    const missing =
                      isConfigured && required > 0
                        ? Math.max(0, required - assigned)
                        : 0;

                    const trancheBadgeVariant: CoverageVariant =
                      !isConfigured
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

                    return (
                      <div
                        key={t.tranche.id}
                        className="rounded-xl border border-border bg-background p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="truncate text-sm font-semibold text-foreground">
                              {t.tranche.nom}
                            </div>
                            <div className="text-xs tabular-nums text-muted-foreground">
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

                        {assigned > 0 ? (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {t.agents.map((a) => {
                              const matricule = a.code_personnel
                                ? `Matricule: ${a.code_personnel}`
                                : null;

                              return (
                                <Tooltip key={a.id}>
                                  <TooltipTrigger asChild>
                                    <Badge
                                      variant="outline"
                                      tabIndex={0}
                                      className="rounded-full px-2 py-1 text-xs font-normal focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                      aria-label={
                                        matricule
                                          ? `${a.prenom} ${a.nom}. ${matricule}`
                                          : `${a.prenom} ${a.nom}`
                                      }
                                    >
                                      {a.prenom} {a.nom}
                                    </Badge>
                                  </TooltipTrigger>

                                  {matricule ? (
                                    <TooltipContent>{matricule}</TooltipContent>
                                  ) : null}
                                </Tooltip>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="mt-3 text-sm text-muted-foreground">
                            Aucun agent affecté.
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <EmptyBox>Aucune tranche pour ce jour.</EmptyBox>
              )}
            </DrawerSection>
          </>
        )}
      </div>
    </PlanningSheetShell>
  );
}
