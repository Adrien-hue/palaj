"use client";

import * as React from "react";
import type { Agent, AgentDay } from "@/types";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

import { CalendarDays, User, Clock, Info, Moon } from "lucide-react";

import { formatDateFRLong } from "@/utils/date.format";
import { cn } from "@/lib/utils";

// ✅ réutilise le type + le composant de ta timeline
import type { CellSegment } from "@/features/planning-team/DayCell";

function normalizeDayType(t: string) {
  if (t === "absent") return "absence";
  return t;
}

function getDayTypeLabel(t: string) {
  switch (t) {
    case "working":
      return "Travail";
    case "rest":
      return "Repos";
    case "zcot":
      return "ZCOT";
    case "absence":
      return "Absence";
    case "unknown":
      return "Non renseigné";
    default:
      return t;
  }
}

function getDayTypeBadgeVariant(
  t: string
): "default" | "secondary" | "outline" | "destructive" {
  switch (t) {
    case "working":
      return "default";
    case "zcot":
      return "secondary";
    case "rest":
      return "outline";
    case "absence":
      return "destructive";
    case "unknown":
      return "outline";
    default:
      return "outline";
  }
}

function parseHHMMSS(t: string): number {
  const [hh, mm] = t.split(":").map((x) => parseInt(x, 10));
  return hh * 60 + mm;
}

function wrapsMidnight(start: string, end: string) {
  return parseHHMMSS(end) <= parseHHMMSS(start);
}

function SheetEmptyState() {
  return (
    <div className="mt-6 rounded-lg border bg-muted/20 p-4 text-sm text-muted-foreground">
      Aucune journée sélectionnée.
    </div>
  );
}

export function DayDetailsSheet(props: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent: Agent | null;
  day: AgentDay | null;
  segments?: CellSegment[]; // ✅ NEW (tu passes déjà selectedSegments)
}) {
  const { open, onOpenChange, agent, day, segments = [] } = props;

  const normalizedType = day ? normalizeDayType(day.day_type) : null;
  const typeLabel = normalizedType ? getDayTypeLabel(normalizedType) : null;
  const typeVariant = normalizedType
    ? getDayTypeBadgeVariant(normalizedType)
    : "outline";

  const dateLabel = day ? formatDateFRLong(day.day_date) : null;

  const hasTranches = (day?.tranches?.length ?? 0) > 0;
  const isWorking = normalizedType === "working";

  const continuationCount = React.useMemo(
    () => segments.filter((s) => s.isContinuation).length,
    [segments]
  );

  const looksLikeContinuation =
    !!day && !isWorking && (hasTranches || continuationCount > 0);

  const showTimeline = !!day && segments.length > 0;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[420px] sm:w-[520px] p-0">
        <div className="p-6">
          <SheetHeader className="space-y-2">
            <SheetTitle>Détail journée</SheetTitle>

            <SheetDescription className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="inline-flex items-center gap-2">
                  <User className="h-4 w-4" />
                  {agent ? (
                    <span className="font-medium text-foreground">
                      {agent.prenom} {agent.nom}
                    </span>
                  ) : (
                    "—"
                  )}
                </span>

                {day ? (
                  <>
                    <span className="text-muted-foreground/60">·</span>
                    <span className="inline-flex items-center gap-2">
                      <CalendarDays className="h-4 w-4" />
                      <span className="text-foreground/90">{dateLabel}</span>
                    </span>
                  </>
                ) : null}
              </div>

              {day ? (
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={typeVariant} className="rounded-full">
                    {typeLabel}
                  </Badge>

                  {day.is_off_shift ? (
                    <Badge variant="secondary" className="rounded-full">
                      Hors service
                    </Badge>
                  ) : null}

                  {looksLikeContinuation ? (
                    <Badge variant="outline" className="rounded-full">
                      <span className="inline-flex items-center gap-1">
                        <Moon className="h-3.5 w-3.5" />
                        Fin de nuit (J-1)
                      </span>
                    </Badge>
                  ) : null}
                </div>
              ) : null}
            </SheetDescription>
          </SheetHeader>

          {!day ? (
            <SheetEmptyState />
          ) : (
            <div className="mt-6 space-y-4">
              {/* Summary card */}
              <Card className="p-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    <Info className="h-4 w-4 text-muted-foreground" />
                  </div>

                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="text-sm font-medium">Récapitulatif</div>

                    {day.description ? (
                      <div className="text-sm text-foreground/90">
                        {day.description}
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">
                        Aucune description.
                      </div>
                    )}

                    {looksLikeContinuation ? (
                      <div className="text-xs text-muted-foreground">
                        Des tranches sont affichées ici car le service a débuté
                        la veille et se termine sur cette journée.
                        {continuationCount > 0 ? (
                          <span className="ml-1 tabular-nums">
                            ({continuationCount} segment(s))
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                </div>
              </Card>

              {/* ✅ Timeline */}
              {showTimeline ? (
                <>
                  <Card className="p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-medium">Timeline</div>
                      <Badge variant="outline" className="rounded-full tabular-nums">
                        {segments.length}
                      </Badge>
                    </div>

                    {/* Légende simple */}
                    {segments.some((s) => s.isContinuation) ? (
                      <div className="mt-2 text-xs text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <Moon className="h-3.5 w-3.5" />
                          Les segments “Fin de nuit” correspondent à un service commencé la veille.
                        </span>
                      </div>
                    ) : null}
                  </Card>

                  <Separator />
                </>
              ) : (
                <Separator />
              )}

              {/* Tranches */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">Tranches</div>
                  {hasTranches ? (
                    <Badge variant="outline" className="rounded-full tabular-nums">
                      {day.tranches.length}
                    </Badge>
                  ) : null}
                </div>

                {!hasTranches ? (
                  <div className="rounded-lg border bg-muted/10 p-4 text-sm text-muted-foreground">
                    Aucune tranche enregistrée sur ce jour.
                    {segments.length > 0 ? (
                      <div className="mt-1 text-xs text-muted-foreground">
                        La timeline peut contenir des segments provenant de la veille.
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {day.tranches.map((tr) => {
                      const wrap = wrapsMidnight(tr.heure_debut, tr.heure_fin);

                      return (
                        <Card key={tr.id} className="p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="font-medium truncate">{tr.nom}</div>

                              <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                                <Clock className="h-3.5 w-3.5" />
                                <span className="tabular-nums">
                                  {tr.heure_debut} → {tr.heure_fin}
                                </span>

                                {wrap ? (
                                  <Badge
                                    variant="outline"
                                    className="rounded-full text-[10px] px-2 py-0 h-5"
                                  >
                                    passe minuit
                                  </Badge>
                                ) : null}
                              </div>
                            </div>

                            <div className="text-[11px] text-muted-foreground tabular-nums">
                              id:{tr.id}
                            </div>
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="pt-2 text-xs text-muted-foreground">
                Lecture seule — l’édition arrivera dans une prochaine itération.
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
