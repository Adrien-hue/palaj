"use client";

import * as React from "react";
import type { Agent, AgentDay, RhViolation } from "@/types";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Clock, Info, User, CalendarDays } from "lucide-react";

import { formatDateFRLong } from "@/utils/date.format";

import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";
import { DayTypeBadge } from "@/components/planning/DayTypeBadge";

function hhmm(t: string) {
  return (t ?? "").slice(0, 5);
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
  rhViolations?: RhViolation[];
}) {
  const { open, onOpenChange, agent, day, rhViolations } = props;

  const dateLabel = day ? formatDateFRLong(day.day_date) : "Jour";

  const tranches = React.useMemo(() => {
    const list = (day?.tranches ?? []).slice();
    list.sort((a, b) => a.heure_debut.localeCompare(b.heure_debut));
    return list;
  }, [day]);

  const hasTranches = tranches.length > 0;

  const rhList = rhViolations ?? [];
  const rhErrors = rhList.filter((v) => v.severity === "error");
  const rhWarnings = rhList.filter((v) => v.severity === "warning");


  const title = (
    <span className="flex min-w-0 items-center gap-2">
      <span className="truncate">{dateLabel}</span>

      {day ? (
        <DayTypeBadge dayType={day.day_type} />
      ) : (
        <Badge variant="outline" className="rounded-full">
          —
        </Badge>
      )}

      {day?.is_off_shift ? (
        <Badge variant="secondary" className="rounded-full">
          HS
        </Badge>
      ) : null}
    </span>
  );

  const description = (
    <span className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
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
    </span>
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
                <div className="text-sm text-muted-foreground">Aucune description.</div>
              )}
            </div>
          </div>
        </DrawerSection>

        {/* Tranches */}
        <DrawerSection
          variant="surface"
          title="Tranches"
          subtitle="Détail des tranches enregistrées sur ce jour."
          right={
            hasTranches ? (
              <Badge variant="outline" className="rounded-full tabular-nums">
                {tranches.length}
              </Badge>
            ) : null
          }
          className="border-border bg-card"
        >
          {!hasTranches ? (
            <EmptyBox className="border-border text-muted-foreground">
              Aucune tranche enregistrée sur ce jour.
            </EmptyBox>
          ) : (
            <div className="space-y-2">
              {tranches.map((tr) => {
                const wrap = wrapsMidnight(tr.heure_debut, tr.heure_fin);

                return (
                  <Card key={tr.id} className="border-border bg-background p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          {/* pastille couleur */}
                          <span
                            className="h-2.5 w-2.5 rounded-full border"
                            style={{ backgroundColor: tr.color ?? "transparent" }}
                            aria-hidden="true"
                          />
                          <div className="truncate font-medium">{tr.nom}</div>
                        </div>

                        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3.5 w-3.5" />
                          <span className="tabular-nums">
                            {hhmm(tr.heure_debut)} → {hhmm(tr.heure_fin)}
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

                      {/* optionnel : garder l’id mais plus discret */}
                      <Badge
                        variant="outline"
                        className="h-5 rounded-full px-2 py-0 text-[10px] tabular-nums text-muted-foreground"
                        title={`Tranche id ${tr.id}`}
                      >
                        #{tr.id}
                      </Badge>
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
