"use client";

import * as React from "react";
import { startOfMonth, endOfMonth } from "date-fns";

import { PlanningPageHeader } from "@/features/planning-common/components/PlanningPageHeader";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";

import { PosteHeaderSelect } from "@/features/planning-poste/components/PosteHeaderSelect";
import { PostePlanningGrid } from "@/features/planning-poste/components/PostePlanningGrid";
import { usePostePlanning } from "@/features/planning-poste/hooks/usePostePlanning";
import { usePosteCoverage } from "@/features/planning-poste/hooks/usePosteCoverage";

import { buildPostePlanningVm } from "@/features/planning-poste/vm/postePlanning.vm.builder";

import { Card, CardContent } from "@/components/ui/card";
import { formatDateFR, toISODate } from "@/utils/date.format";
import { buildPosteCoverageConfigVm } from "../vm/posteCoverageConfig.vm.builder";

type PosteListItem = { id: number; nom: string };

export function PostePlanningClient({
  initialPosteId = null,
  initialAnchor,
  postes,
}: {
  initialPosteId?: number | null;
  initialAnchor: string; // YYYY-MM-01
  postes: PosteListItem[];
}) {
  const [posteId, setPosteId] = React.useState<number | null>(initialPosteId);

  const [period, setPeriod] = React.useState<PlanningPeriod>(() => {
    const base = startOfMonth(new Date(initialAnchor + "T00:00:00"));
    return { kind: "month", month: base };
  });

  const range = React.useMemo(() => {
    if (period.kind === "month") {
      const start = startOfMonth(period.month);
      const end = endOfMonth(period.month);
      return { start: toISODate(start), end: toISODate(end), isRange: false };
    }
    return {
      start: toISODate(period.start),
      end: toISODate(period.end),
      isRange: true,
    };
  }, [period]);

  const anchorMonth = React.useMemo(() => {
    if (period.kind === "month") return toISODate(startOfMonth(period.month));
    return toISODate(startOfMonth(new Date(range.start + "T00:00:00")));
  }, [period, range.start]);

  const subtitle = React.useMemo(() => {
    return range.isRange
      ? `Couverture du ${formatDateFR(range.start)} au ${formatDateFR(range.end)}`
      : "Couverture mensuelle";
  }, [range.start, range.end, range.isRange]);

  const planning = usePostePlanning({
    posteId,
    startDate: range.start,
    endDate: range.end,
  });

  const coverage = usePosteCoverage({ posteId });

  const coverageConfigVm = React.useMemo(() => {
    if (!coverage.data) return null;
    return buildPosteCoverageConfigVm(coverage.data);
  }, [coverage.data]);

  const planningVm = React.useMemo(() => {
    if (!planning.data) return null;
    return buildPostePlanningVm(planning.data, {
      coverageConfig: coverageConfigVm,
    });
  }, [planning.data, coverageConfigVm]);

  const planningError = planning.error ?? null;
  const coverageWarning = coverage.error ?? null;

  const isLoading = planning.isLoading;

  const isValidating = planning.isValidating;

  const headerSubtitle =
    posteId === null
      ? subtitle
      : isLoading
        ? "Chargement…"
        : planningError
          ? "Erreur de chargement du planning"
          : isValidating
            ? "Mise à jour…"
            : subtitle;

  const coverageStatusText =
    posteId !== null && coverageWarning ? "Couverture indisponible" : null;

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        titleSlot={
          <PosteHeaderSelect
            postes={postes}
            valueId={posteId}
            onChange={(id) => setPosteId(id)}
          />
        }
        subtitle={headerSubtitle}
        rightSlot={
          <PlanningPeriodControls
            value={period}
            onChange={setPeriod}
            onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
            onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
            disabled={posteId !== null && isLoading}
          />
        }
      />

      {posteId === null ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Veuillez sélectionner un poste pour afficher sa couverture.
          </CardContent>
        </Card>
      ) : planningError ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Impossible de charger la couverture. {(planningError as Error).message}
          </CardContent>
        </Card>
      ) : planningVm ? (
        range.isRange ? (
          <PostePlanningGrid
            mode="range"
            startDate={range.start}
            endDate={range.end}
            planning={planningVm}
          />
        ) : (
          <PostePlanningGrid
            mode="month"
            anchorMonth={anchorMonth}
            planning={planningVm}
          />
        )
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Chargement…
          </CardContent>
        </Card>
      )}
    </div>
  );
}
