"use client";

import * as React from "react";
import type { Agent, AgentDay } from "@/types";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Clock, Info, Moon, User, CalendarDays } from "lucide-react";

import { formatDateFRLong } from "@/utils/date.format";

// ✅ réutilise le type de ta timeline
import type { CellSegment } from "@/features/planning-team/DayCell";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";

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

export function TeamDaySheet(props: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent: Agent | null;
  day: AgentDay | null;
  segments?: CellSegment[];
}) {
  const { open, onOpenChange, agent, day, segments = [] } = props;

  const normalizedType = day ? normalizeDayType(day.day_type) : null;
  const typeLabel = normalizedType ? getDayTypeLabel(normalizedType) : null;
  const typeVariant = normalizedType
    ? getDayTypeBadgeVariant(normalizedType)
    : "outline";

  const dateLabel = day ? formatDateFRLong(day.day_date) : "Jour";

  const hasTranches = (day?.tranches?.length ?? 0) > 0;
  const isWorking = normalizedType === "working";

  const continuationCount = React.useMemo(
    () => segments.filter((s) => s.isContinuation).length,
    [segments]
  );

  const looksLikeContinuation =
    !!day && !isWorking && (hasTranches || continuationCount > 0);

  const showTimeline = !!day && segments.length > 0;

  const title = (
    <span className="flex min-w-0 items-center gap-2">
      <span className="truncate">{dateLabel}</span>

      {day ? (
        <Badge variant={typeVariant} className="rounded-full">
          {typeLabel}
        </Badge>
      ) : (
        <Badge variant="outline" className="rounded-full">
          —
        </Badge>
      )}

      {day?.is_off_shift ? (
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
    </span>
  );

  const description = (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          <User className="h-4 w-4" />
          <span className="text-foreground">
            {agent ? `${agent.prenom} ${agent.nom}` : "—"}
          </span>
        </span>

        {day ? (
          <>
            <span className="text-muted-foreground/60">·</span>
            <span className="inline-flex items-center gap-2">
              <CalendarDays className="h-4 w-4" />
              <span className="text-foreground/90">{formatDateFRLong(day.day_date)}</span>
            </span>
          </>
        ) : null}
      </div>
    </div>
  );

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={onOpenChange}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      rootClassName="bg-background"
      bodyClassName="p-4"
      title={title}
      description={description}
      isEmpty={!day}
      empty={<EmptyBox>Aucune journée sélectionnée.</EmptyBox>}
    >
      <div className="space-y-4">
        {/* Récap */}
        <DrawerSection
          variant="surface"
          title="Récapitulatif"
          subtitle="Informations générales de la journée."
          className="border-border bg-card"
        >
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <div className="min-w-0 flex-1 space-y-2">
              {day?.description ? (
                <div className="text-sm text-foreground/90">{day.description}</div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Aucune description.
                </div>
              )}

              {looksLikeContinuation ? (
                <div className="text-xs text-muted-foreground">
                  Des tranches sont affichées ici car le service a débuté la veille
                  et se termine sur cette journée.
                  {continuationCount > 0 ? (
                    <span className="ml-1 tabular-nums">
                      ({continuationCount} segment(s))
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        </DrawerSection>

        {/* Timeline (placeholder pour l’instant) */}
        <DrawerSection
          variant="surface"
          title="Timeline"
          subtitle="Vue synthétique des segments."
          right={
            showTimeline ? (
              <Badge variant="outline" className="rounded-full tabular-nums">
                {segments.length}
              </Badge>
            ) : null
          }
          className="border-border bg-card"
        >
          {!showTimeline ? (
            <EmptyBox className="border-border text-muted-foreground">
              Aucune timeline à afficher.
            </EmptyBox>
          ) : (
            <>
              {segments.some((s) => s.isContinuation) ? (
                <div className="mb-3 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Moon className="h-3.5 w-3.5" />
                    Les segments “Fin de nuit” correspondent à un service commencé la veille.
                  </span>
                </div>
              ) : null}

              {/* Ici tu pourras brancher ton composant timeline si tu en as un */}
              <div className="text-sm text-muted-foreground">
                (Timeline à brancher ici)
              </div>
            </>
          )}
        </DrawerSection>

        {/* Tranches */}
        <DrawerSection
          variant="surface"
          title="Tranches"
          subtitle="Détail des tranches enregistrées sur ce jour."
          right={
            hasTranches ? (
              <Badge variant="outline" className="rounded-full tabular-nums">
                {day?.tranches.length}
              </Badge>
            ) : null
          }
          className="border-border bg-card"
        >
          {!hasTranches ? (
            <EmptyBox className="border-border text-muted-foreground">
              Aucune tranche enregistrée sur ce jour.
              {segments.length > 0 ? (
                <div className="mt-1 text-xs text-muted-foreground">
                  La timeline peut contenir des segments provenant de la veille.
                </div>
              ) : null}
            </EmptyBox>
          ) : (
            <div className="space-y-2">
              {day!.tranches.map((tr) => {
                const wrap = wrapsMidnight(tr.heure_debut, tr.heure_fin);

                return (
                  <Card key={tr.id} className="border-border bg-background p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate font-medium">{tr.nom}</div>

                        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3.5 w-3.5" />
                          <span className="tabular-nums">
                            {tr.heure_debut} → {tr.heure_fin}
                          </span>

                          {wrap ? (
                            <Badge
                              variant="outline"
                              className="h-5 rounded-full px-2 py-0 text-[10px]"
                            >
                              passe minuit
                            </Badge>
                          ) : null}
                        </div>
                      </div>

                      <div className="tabular-nums text-[11px] text-muted-foreground">
                        id:{tr.id}
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </DrawerSection>

        <div className="pt-1 text-xs text-muted-foreground">
          Lecture seule — l’édition arrivera dans une prochaine itération.
        </div>
      </div>
    </PlanningSheetShell>
  );
}
