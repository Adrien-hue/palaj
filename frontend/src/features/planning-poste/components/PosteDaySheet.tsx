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

import { timeLabelHHMM } from "@/utils/time.format";
import { X } from "lucide-react";

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

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg p-0">
        {/* Background wrapper */}
        <div className="h-full bg-[color:var(--app-bg)]">
          {/* Top area (sticky) */}
          <div className="sticky top-0 z-10 border-b border-[color:var(--app-border)] bg-[color:var(--app-surface)]/95 backdrop-blur p-4">
            <SheetHeader className="space-y-2">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <SheetTitle>
                    <span className="flex items-center gap-2 min-w-0">
                      <span className="truncate">
                        {day ? formatDateFRLong(day.day_date) : "Jour"}
                      </span>

                      <Badge
                        variant={coverageVariant(total, covered)}
                        className="shrink-0 tabular-nums"
                        title={
                          total === 0
                            ? "Aucune tranche"
                            : covered >= total
                            ? "Couverture complète"
                            : "Couverture incomplète"
                        }
                      >
                        {total > 0 ? `${covered}/${total}` : "—"}
                      </Badge>
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
                    title="Fermer"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </SheetClose>
              </div>
            </SheetHeader>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            {day?.description ? (
              <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-3 text-sm text-[color:var(--app-muted)]">
                {day.description}
              </div>
            ) : null}

            {day?.is_off_shift ? (
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

              {day?.tranches.length ? (
                <div className="space-y-2">
                  {sortTranchesForCoverage(day.tranches).map((t) => {
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
                            {t.agents.map((a) => (
                              <span
                                key={a.id}
                                className="inline-flex items-center rounded-full border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-2 py-1 text-xs text-[color:var(--app-text)]"
                                title={
                                  a.code_personnel
                                    ? `Matricule: ${a.code_personnel}`
                                    : undefined
                                }
                              >
                                {a.prenom} {a.nom}
                              </span>
                            ))}
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
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
