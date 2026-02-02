"use client";

import * as React from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DayTimeline } from "@/components/planning/timeline/DayTimeline"; // adapte le chemin

import type { TranchesTimelineProps } from "./types";
import { formatHHMM, trancheToSegments } from "./helpers";

const TOTAL_MINUTES = 1440;

export default function TranchesTimeline({
  tranches,
  markerEveryHours = 3,
  onSelectTranche,
}: TranchesTimelineProps) {
  const ticksHours = React.useMemo(() => {
    const res: number[] = [];
    for (let h = 0; h <= 24; h += markerEveryHours) res.push(h);
    return res;
  }, [markerEveryHours]);

  const range = React.useMemo(() => ({ startMin: 0, endMin: TOTAL_MINUTES }), []);

  const segments = React.useMemo(() => {
    return tranches.flatMap((t) => {
      const parts = trancheToSegments(t.heure_debut, t.heure_fin);
      return parts.map((p, idx) => ({
        ...t,
        startMin: p.startMin,
        endMin: p.endMin,
        // id unique par segment si tranche split overnight
        _segKey: `${t.id}-${idx}`,
      }));
    });
  }, [tranches]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Timeline (24h)</CardTitle>
        <p className="text-xs text-muted-foreground">
          Survolez une tranche pour voir les heures exactes, cliquez pour la sélectionner.
        </p>
      </CardHeader>

      <CardContent className="pt-0">
        <DayTimeline
          segments={segments}
          range={range}
          startLabel="00:00"
          endLabel="24:00"
          ticksHours={ticksHours}
          getId={(s) => s._segKey}
          getLabel={(s) => s.nom}
          getTooltip={(s) => {
            const tooltipText = `${s.nom} — ${formatHHMM(s.heure_debut)} → ${formatHHMM(s.heure_fin)}`;
            return (
              <div className="flex items-center gap-2 text-xs">
                {s.color ? (
                  <span
                    className="h-2.5 w-2.5 rounded-sm border"
                    style={{ backgroundColor: s.color }}
                    aria-hidden="true"
                  />
                ) : null}
                <span>{tooltipText}</span>
              </div>
            );
          }}
          barClassName={(s) =>
            [
              "cursor-pointer",
              "text-primary-foreground",
              // fallback si pas de couleur
              s.color ? "" : "bg-primary/80 ring-1 ring-primary/10",
            ].join(" ")
          }
          barStyle={(s) =>
            s.color
              ? {
                  backgroundColor: s.color,
                }
              : undefined
          }
          textClassName={() => ""}
          onBarClick={(s) => onSelectTranche?.(s.id)}
        />
      </CardContent>
    </Card>
  );
}
