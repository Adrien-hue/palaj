"use client";

import { useMemo } from "react";
import { X } from "lucide-react";

import type { Poste } from "@/types/postes";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SheetClose } from "@/components/ui/sheet";
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

function coverageVariant(total: number, covered: number) {
  if (total === 0) return "secondary";
  if (covered >= total) return "success";
  return "warning";
}

function coverageLabel(total: number, covered: number) {
  if (total === 0) return "Aucune tranche";
  if (covered >= total) return "Couverture complète";
  return "Couverture incomplète";
}

function sortTranchesForCoverage<
  T extends { tranche: { heure_debut: string; nom: string }; agents: any[] }
>(tranches: T[]) {
  return [...tranches].sort((a, b) => {
    const aMissing = (a.agents?.length ?? 0) === 0;
    const bMissing = (b.agents?.length ?? 0) === 0;

    if (aMissing !== bMissing) return aMissing ? -1 : 1;

    const ha = (a.tranche.heure_debut ?? "").slice(0, 8);
    const hb = (b.tranche.heure_debut ?? "").slice(0, 8);
    if (ha !== hb) return ha.localeCompare(hb);

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
  const total = day?.coverage.total ?? 0;
  const covered = day?.coverage.covered ?? 0;

  const sortedTranches = useMemo(
    () => (day?.tranches?.length ? sortTranchesForCoverage(day.tranches) : []),
    [day?.tranches]
  );

  const coverageText = `${coverageLabel(total, covered)} • ${
    total > 0 ? `${covered}/${total}` : "—"
  }`;

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
                  variant={coverageVariant(total, covered)}
                  className="shrink-0 tabular-nums"
                  tabIndex={0}
                  aria-label={coverageText}
                >
                  {total > 0 ? `${covered}/${total}` : "—"}
                </Badge>
              </TooltipTrigger>
              <TooltipContent>{coverageText}</TooltipContent>
            </Tooltip>
          </span>
        }
        description={
          <span className="truncate">{poste.nom} • Détail des tranches</span>
        }
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
                      const has = t.agents.length > 0;

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

                            <Badge
                              variant={has ? "success" : "warning"}
                              className="shrink-0"
                            >
                              {has ? `${t.agents.length} agent(s)` : "Non couvert"}
                            </Badge>
                          </div>

                          {has ? (
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
