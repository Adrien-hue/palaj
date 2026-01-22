"use client";

import type { Poste } from "@/types/postes";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { timeLabelHHMM } from "@/utils/time.format";
import { X } from "lucide-react";
import { useMemo } from "react";

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
    <TooltipProvider>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full p-0 sm:max-w-lg">
          <div className="h-full bg-[color:var(--app-bg)]">
            {/* Top area (sticky) */}
            <div className="sticky top-0 z-10 border-b border-[color:var(--app-border)] bg-[color:var(--app-surface)]/95 backdrop-blur p-4">
              <SheetHeader className="space-y-2">
                <div className="flex items-start gap-3">
                  <div className="min-w-0 flex-1">
                    <SheetTitle>
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
                    </SheetTitle>

                    <SheetDescription className="truncate">
                      {poste.nom} • Détail des tranches
                    </SheetDescription>
                  </div>

                  <SheetClose asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="shrink-0"
                      aria-label="Fermer"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </SheetClose>
                </div>
              </SheetHeader>
            </div>

            {/* Content */}
            <div className="space-y-4 p-4">
              {!day ? (
                <div className="rounded-xl border border-dashed border-[color:var(--app-border)] p-4 text-sm text-[color:var(--app-muted)]">
                  Aucun jour sélectionné.
                </div>
              ) : (
                <>
                  {day.description ? (
                    <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-3 text-sm text-[color:var(--app-muted)]">
                      {day.description}
                    </div>
                  ) : null}

                  {day.is_off_shift ? (
                    <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-soft)] p-3 text-sm text-[color:var(--app-text)]">
                      Poste indiqué comme “OFF” ce jour.
                    </div>
                  ) : null}

                  <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-3">
                    <div className="text-sm font-semibold text-[color:var(--app-text)]">
                      Tranches
                    </div>
                    <div className="mt-1 text-xs text-[color:var(--app-muted)]">
                      Détail des affectations par tranche.
                    </div>

                    <Separator className="my-3" />

                    {sortedTranches.length ? (
                      <div className="space-y-2">
                        {sortedTranches.map((t) => {
                          const has = t.agents.length > 0;

                          return (
                            <div
                              key={t.tranche.id}
                              className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-bg)] p-3"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="min-w-0">
                                  <div className="truncate text-sm font-semibold text-[color:var(--app-text)]">
                                    {t.tranche.nom}
                                  </div>
                                  <div className="text-xs tabular-nums text-[color:var(--app-muted)]">
                                    {timeLabelHHMM(t.tranche.heure_debut)}–
                                    {timeLabelHHMM(t.tranche.heure_fin)}
                                  </div>
                                </div>

                                <Badge
                                  variant={has ? "success" : "warning"}
                                  className="shrink-0"
                                >
                                  {has
                                    ? `${t.agents.length} agent(s)`
                                    : "Non couvert"}
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
                                            className="rounded-full px-2 py-1 text-xs font-normal focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring)]"
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
                                          <TooltipContent>
                                            {matricule}
                                          </TooltipContent>
                                        ) : null}
                                      </Tooltip>
                                    );
                                  })}
                                </div>
                              ) : (
                                <div className="mt-3 text-sm text-[color:var(--app-muted)]">
                                  Aucun agent affecté.
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="rounded-xl border border-dashed border-[color:var(--app-border)] p-4 text-sm text-[color:var(--app-muted)]">
                        Aucune tranche pour ce jour.
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </TooltipProvider>
  );
}
