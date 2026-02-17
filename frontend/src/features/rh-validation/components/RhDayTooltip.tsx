"use client";

import * as React from "react";
import type { RhViolation } from "@/types/rhValidation";

import { Badge } from "@/components/ui/badge";
import { DayTypeBadge, dayTypeLabel } from "@/components/planning/DayTypeBadge";
import { formatDateFRLong } from "@/utils/date.format";

type Window = { start: string; end: string };

type TrancheLike = {
  id: number;
  nom: string;
  heure_debut: string; // "HH:MM:SS"
  heure_fin: string;   // "HH:MM:SS"
  color?: string | null;
};

function hhmm(t: string) {
  return (t ?? "").slice(0, 5);
}
function parseHHMMSS(t: string): number {
  const [hh, mm] = (t ?? "00:00").split(":").map((x) => parseInt(x, 10));
  return hh * 60 + mm;
}
function wrapsMidnight(start: string, end: string) {
  return parseHHMMSS(end) <= parseHHMMSS(start);
}

function severityLabel(s: RhViolation["severity"]) {
  if (s === "error") return "Erreur RH";
  if (s === "warning") return "Alerte RH";
  return "Info RH";
}

function severityBadgeVariant(
  s: RhViolation["severity"],
): React.ComponentProps<typeof Badge>["variant"] {
  if (s === "error") return "destructive";
  if (s === "warning") return "secondary";
  return "outline";
}

function sortRh(violations: RhViolation[]) {
  const rank = (s: RhViolation["severity"]) => (s === "error" ? 0 : s === "warning" ? 1 : 2);
  return violations.slice().sort((a, b) => rank(a.severity) - rank(b.severity));
}

export function RhDayTooltip({
  dateISO,
  dayType,
  description,
  windows,
  tranches,
  isOffShift,
  rhViolations,
  showRhInfos = true,
}: {
  dateISO: string; // "YYYY-MM-DD"
  dayType: string;
  description?: string | null;
  windows?: Window[];
  tranches?: TrancheLike[];
  isOffShift?: boolean;
  rhViolations: RhViolation[];
  /** Par défaut: true (comme Agent). Pour Team tu peux passer false. */
  showRhInfos?: boolean;
}) {
  const dateLabel = formatDateFRLong(dateISO);

  const rhSorted = React.useMemo(() => sortRh(rhViolations ?? []), [rhViolations]);
  const rhErrors = rhSorted.filter((v) => v.severity === "error");
  const rhWarnings = rhSorted.filter((v) => v.severity === "warning");
  const rhInfos = rhSorted.filter((v) => v.severity === "info");

  const hasWindows = (windows?.length ?? 0) > 0;
  const hasTranches = (tranches?.length ?? 0) > 0;

  const trSorted = React.useMemo(() => {
    return (tranches ?? []).slice().sort((a, b) => a.heure_debut.localeCompare(b.heure_debut));
  }, [tranches]);

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-medium">{dateLabel}</div>
        <div className="flex items-center gap-2">
          <DayTypeBadge dayType={dayType as any} />
          {isOffShift ? (
            <Badge variant="secondary" className="h-5 rounded-full px-2 py-0 text-[10px]">
              HS
            </Badge>
          ) : null}
        </div>
      </div>

      {description ? (
        <div className="text-xs text-muted-foreground line-clamp-2">{description}</div>
      ) : null}

      {/* Hours / tranches */}
      {hasWindows ? (
        <div className="space-y-1">
          <div className="text-xs font-medium">Horaires</div>
          {(windows ?? []).slice(0, 4).map((w, i) => (
            <div key={i} className="flex items-center justify-between gap-2 text-xs tabular-nums text-muted-foreground">
              <span>
                {w.start.slice(0, 5)} – {w.end.slice(0, 5)}
              </span>
            </div>
          ))}
          {(windows?.length ?? 0) > 4 ? (
            <div className="text-[11px] text-muted-foreground">+{(windows?.length ?? 0) - 4} plage(s)</div>
          ) : null}
        </div>
      ) : hasTranches ? (
        <div className="space-y-1">
          <div className="text-xs font-medium">Tranches</div>
          {trSorted.slice(0, 4).map((tr) => {
            const wrap = wrapsMidnight(tr.heure_debut, tr.heure_fin);
            return (
              <div key={tr.id} className="flex items-center justify-between gap-3">
                <div className="min-w-0 flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full border"
                    style={{ backgroundColor: tr.color ?? "transparent" }}
                    aria-hidden="true"
                  />
                  <span className="truncate text-xs font-medium">{tr.nom}</span>
                </div>

                <div className="shrink-0 flex items-center gap-2 text-[11px] tabular-nums text-muted-foreground">
                  <span>
                    {hhmm(tr.heure_debut)}–{hhmm(tr.heure_fin)}
                  </span>
                  {wrap ? (
                    <Badge variant="outline" className="h-5 rounded-full px-2 py-0 text-[10px]">
                      passe minuit
                    </Badge>
                  ) : null}
                </div>
              </div>
            );
          })}
          {trSorted.length > 4 ? (
            <div className="text-[11px] text-muted-foreground">+{trSorted.length - 4} tranche(s)</div>
          ) : null}
        </div>
      ) : (
        <div className="text-xs text-muted-foreground">{dayTypeLabel(dayType as any)}</div>
      )}

      {/* RH */}
      {rhSorted.length > 0 ? (
        <div className="space-y-1 pt-1">
          <div className="text-xs font-medium">Contrôle RH</div>

          {rhErrors.length > 0 ? (
            <div className="space-y-1">
              {rhErrors.slice(0, 3).map((v, i) => (
                <div key={`e-${v.code}-${i}`} className="flex items-start gap-2">
                  <Badge
                    variant={severityBadgeVariant(v.severity)}
                    className="h-5 rounded-full px-2 py-0 text-[10px]"
                  >
                    {severityLabel(v.severity)}
                  </Badge>
                  <div className="min-w-0 text-xs text-muted-foreground">{v.message}</div>
                </div>
              ))}
              {rhErrors.length > 3 ? (
                <div className="text-[11px] text-muted-foreground">+{rhErrors.length - 3} erreur(s)</div>
              ) : null}
            </div>
          ) : null}

          {rhWarnings.length > 0 ? (
            <div className="space-y-1">
              {rhWarnings.slice(0, 2).map((v, i) => (
                <div key={`w-${v.code}-${i}`} className="flex items-start gap-2">
                  <Badge
                    variant={severityBadgeVariant(v.severity)}
                    className="h-5 rounded-full px-2 py-0 text-[10px]"
                  >
                    {severityLabel(v.severity)}
                  </Badge>
                  <div className="min-w-0 text-xs text-muted-foreground">{v.message}</div>
                </div>
              ))}
              {rhWarnings.length > 2 ? (
                <div className="text-[11px] text-muted-foreground">+{rhWarnings.length - 2} alerte(s)</div>
              ) : null}
            </div>
          ) : null}

          {showRhInfos && rhInfos.length > 0 ? (
            <div className="text-[11px] text-muted-foreground">{rhInfos.length} info(s) RH</div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
