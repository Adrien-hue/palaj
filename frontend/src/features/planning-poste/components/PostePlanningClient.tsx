"use client";

import * as React from "react";
import { startOfMonth, endOfMonth } from "date-fns";

import { PlanningPageHeader } from "@/features/planning-common/components/PlanningPageHeader";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";

import { PosteHeaderSelect } from "@/features/planning-poste/components/PosteHeaderSelect";
import { PostePlanningGrid } from "@/features/planning-poste/components/PostePlanningGrid";
import { PosteDaySheet } from "@/features/planning-poste/components/PosteDaySheet";
import { PosteBulkEditSheet } from "@/features/planning-poste/components/PosteBulkEditSheet";

import { usePostePlanning } from "@/features/planning-poste/hooks/usePostePlanning";
import { usePosteCoverage } from "@/features/planning-poste/hooks/usePosteCoverage";
import { usePostePlanningActions } from "@/features/planning-poste/hooks/usePostePlanningActions";
import { usePosteTranches } from "@/features/planning-poste/hooks/usePosteTranches";
import { buildPostePlanningVm } from "@/features/planning-poste/vm/postePlanning.vm.builder";

import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Switch } from "@/components/ui/switch";
import { formatDateFR, toISODate } from "@/utils/date.format";
import { buildPosteCoverageConfigVm } from "../vm/posteCoverageConfig.vm.builder";
import { useQualifiedAgents } from "../hooks/useQualifiedAgents";

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

  const qualifiedAgents = useQualifiedAgents(posteId);

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

  const actions = usePostePlanningActions({
    posteId,
    mutatePlanning: planning.mutate,
  });

  // ---------------- Single selection ----------------

  const [selectedDate, setSelectedDate] = React.useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = React.useState(false);

  const closeSheet = React.useCallback(() => {
    setSheetOpen(false);
    setSelectedDate(null);
  }, []);

  // -------------------- Multi selection --------------------
  const [multiSelect, setMultiSelect] = React.useState(false);
  const [selectedDates, setSelectedDates] = React.useState<Set<string>>(
    () => new Set(),
  );
  const [anchorDate, setAnchorDate] = React.useState<string | null>(null);
  const [bulkOpen, setBulkOpen] = React.useState(false);

  const clearMultiSelection = React.useCallback(() => {
    setSelectedDates(new Set());
    setAnchorDate(null);
  }, []);

  const toggleMultiSelect = React.useCallback(() => {
    setMultiSelect((v) => {
      const next = !v;
      if (next) {
        // en entrant en multi => on ferme la sheet single
        setSheetOpen(false);
        setSelectedDate(null);
        clearMultiSelection();
      } else {
        clearMultiSelection();
      }
      return next;
    });
  }, [clearMultiSelection]);

  const exitMultiSelect = React.useCallback(() => {
    setMultiSelect(false);
    clearMultiSelection();
  }, [clearMultiSelection]);

  const selectedCount = selectedDates.size;

  const selectedDatesSorted = React.useMemo(
    () => Array.from(selectedDates).sort((a, b) => a.localeCompare(b)),
    [selectedDates],
  );

  const handleMultiSelectDay = React.useCallback(
    (iso: string, e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();

      setSelectedDates((prev) => {
        const next = new Set(prev);

        if (e.shiftKey && anchorDate && planningVm) {
          const ordered = planningVm.days
            .map((d) => d.day_date)
            .slice()
            .sort((a, b) => a.localeCompare(b));

          const a = ordered.indexOf(anchorDate);
          const b = ordered.indexOf(iso);

          if (a !== -1 && b !== -1) {
            const [start, end] = a < b ? [a, b] : [b, a];
            for (let i = start; i <= end; i++) next.add(ordered[i]);
            return next;
          }
        }

        if (next.has(iso)) next.delete(iso);
        else next.add(iso);

        return next;
      });

      setAnchorDate((prev) => (e.shiftKey ? (prev ?? iso) : iso));
    },
    [anchorDate, planningVm],
  );

  // reset selection on poste/period change
  React.useEffect(() => {
    setSelectedDate(null);
    setSheetOpen(false);
    setMultiSelect(false);
    clearMultiSelection();
  }, [posteId, range.start, range.end, clearMultiSelection]);

  // Ensure ESC closes everything (capture)
  React.useEffect(() => {
    if (!sheetOpen) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      e.preventDefault();
      e.stopPropagation();
      closeSheet();
    };

    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, [sheetOpen, closeSheet]);

  const selectedDayVm = React.useMemo(() => {
    if (!planningVm || !selectedDate) return null;
    return planningVm.days.find((d) => d.day_date === selectedDate) ?? null;
  }, [planningVm, selectedDate]);

  const handleSelectedDateChange = React.useCallback(
    (d: string | null) => {
      setSelectedDate(d);
      if (d && planningVm) setSheetOpen(true);
    },
    [planningVm],
  );

  const posteTranches = usePosteTranches(posteId);

  const bulkTranches = React.useMemo(() => {
    return (posteTranches.data ?? []).map((t) => ({
      id: t.id,
      nom: t.nom,
      heure_debut: t.heure_debut,
      heure_fin: t.heure_fin,
      color: t.color ?? null,
    }));
  }, [posteTranches.data]);

  // ---------------- UI state ----------------

  const planningError = planning.error ?? null;
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

  const canShowGrid = posteId !== null && !planningError && !!planningVm;

  const poste = planning.data?.poste;

  return (
    <div className="space-y-4">
      <PlanningPageHeader
        titleSlot={
          <PosteHeaderSelect
            postes={postes}
            valueId={posteId}
            onChange={setPosteId}
          />
        }
        subtitle={headerSubtitle}
        rightSlot={
          <div className="flex items-center gap-4">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-pointer">
                  <Switch
                    id="poste-multi-select"
                    checked={multiSelect}
                    onCheckedChange={toggleMultiSelect}
                  />
                  <Label htmlFor="poste-multi-select">Sélection multiple</Label>
                </div>
              </TooltipTrigger>

              <TooltipContent side="bottom" align="start">
                <p className="text-sm">
                  Sélectionnez plusieurs jours pour modifier les affectations
                  <br />
                  en une seule fois.
                </p>
              </TooltipContent>
            </Tooltip>
            <PlanningPeriodControls
              value={period}
              onChange={setPeriod}
              onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
              onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
              disabled={posteId !== null && isLoading}
            />
          </div>
        }
      />

      {multiSelect ? (
        <div className="sticky top-0 z-10">
          <div className="rounded-xl border bg-card/95 p-3 shadow-sm backdrop-blur">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">
                  {selectedCount}{" "}
                  {selectedCount > 1
                    ? "jours sélectionnés"
                    : "jour sélectionné"}
                </span>
                {selectedCount === 0 ? (
                  <span className="text-muted-foreground">
                    — cliquez pour sélectionner, Shift pour une plage
                  </span>
                ) : null}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={clearMultiSelection}
                  disabled={selectedCount === 0}
                >
                  Tout désélectionner
                </Button>

                <Button
                  type="button"
                  onClick={() => setBulkOpen(true)}
                  disabled={selectedCount === 0}
                >
                  Éditer
                </Button>

                <Button type="button" variant="ghost" onClick={exitMultiSelect}>
                  Quitter
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {posteId === null ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Veuillez sélectionner un poste pour afficher sa couverture.
          </CardContent>
        </Card>
      ) : planningError ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Impossible de charger la couverture.{" "}
            {(planningError as Error).message}
          </CardContent>
        </Card>
      ) : canShowGrid ? (
        range.isRange ? (
          <PostePlanningGrid
            mode="range"
            startDate={range.start}
            endDate={range.end}
            planning={planningVm}
            multiSelect={multiSelect}
            multiSelectedDates={selectedDates}
            onMultiSelectDay={(day, e) => handleMultiSelectDay(day.day_date, e)}
            onDayClick={(day) => {
              if (multiSelect) return;
              setSelectedDate(day.day_date);
              setSheetOpen(true);
            }}
          />
        ) : (
          <PostePlanningGrid
            mode="month"
            anchorMonth={anchorMonth}
            planning={planningVm}
            multiSelect={multiSelect}
            multiSelectedDates={selectedDates}
            onMultiSelectDay={(day, e) => handleMultiSelectDay(day.day_date, e)}
            onDayClick={(day) => {
              if (multiSelect) return;
              setSelectedDate(day.day_date);
              setSheetOpen(true);
            }}
          />
        )
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Chargement…
          </CardContent>
        </Card>
      )}

      {/* Sheet extraite */}
      {posteId !== null && planning.data?.poste ? (
        <PosteDaySheet
          open={sheetOpen}
          onClose={closeSheet}
          day={selectedDayVm}
          poste={planning.data.poste}
          availableAgents={qualifiedAgents.agents ?? []}
          isAgentsLoading={qualifiedAgents.isLoading}
          isSaving={actions.isSaving}
          isDeleting={actions.isDeleting}
          onSaveDay={actions.saveDay}
          onDeleteDay={actions.deleteDay}
        />
      ) : null}

      {posteId !== null && poste ? (
        <PosteBulkEditSheet
          open={bulkOpen}
          onClose={() => setBulkOpen(false)}
          posteId={posteId}
          poste={poste}
          selectedDates={selectedDatesSorted}
          availableAgents={qualifiedAgents.agents ?? []}
          isAgentsLoading={qualifiedAgents.isLoading}
          tranches={bulkTranches}
          onSaveDay={actions.saveDay}
          onApplied={() => clearMultiSelection()}
        />
      ) : null}
    </div>
  );
}
