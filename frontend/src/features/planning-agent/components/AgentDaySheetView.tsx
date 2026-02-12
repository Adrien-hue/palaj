"use client";

import { RhViolation } from "@/types";
import { useEffect, useMemo, useState } from "react";
import type { AgentDayVm } from "../vm/agentPlanning.vm";
import { formatDateFR } from "@/utils/date.format";
import { AgentDayGantt } from "./AgentDayGantt";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { DayTypeBadge } from "@/components/planning/DayTypeBadge";
import { EmptyBox } from "@/components/planning/DrawerSection";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";

import { QualifiedTrancheSelect } from "@/features/planning-agent/components/QualifiedTrancheSelect";
import { DayTypeSelect } from "@/components/planning/DayTypeSelect";
import { cn } from "@/lib/utils";
import { usePosteNamesById } from "@/features/postes/hooks/usePosteNamesById";

export type AgentDaySheetSavePayload = {
  dayDate: string;
  day_type: string;
  description: string | null;
  tranche_id: number | null;
};

type Props = {
  open: boolean;
  onClose: () => void;
  day: AgentDayVm | null;
  agentId: number;
  onSave: (payload: AgentDaySheetSavePayload) => Promise<void>;
  onDelete: (dayDate: string) => Promise<void>;

  // ✅ états réseau / UI
  loading?: boolean;
  validating?: boolean;
  busy?: boolean;
  loadError?: string | null;
  actionError?: string | null;
  rhViolations?: RhViolation[];
};

export function AgentDaySheetView({
  open,
  onClose,
  day,
  agentId,
  onSave,
  onDelete,

  loading = false,
  validating = false,
  busy = false,
  loadError = null,
  actionError = null,
  rhViolations = [],
}: Props) {
  const dateLabel = day ? formatDateFR(day.day_date) : "Jour";
  const [coverageRefreshKey, setCoverageRefreshKey] = useState(0);

  const [dayType, setDayType] = useState<string>("rest");
  const [description, setDescription] = useState<string>("");
  const [trancheId, setTrancheId] = useState<number | null>(null);

  useEffect(() => {
    if (!day) return;
    setDayType(day.day_type ?? "rest");
    setDescription(day.description ?? "");
    setTrancheId(day.tranche_id ?? null);
  }, [day]);

  const segmentPosteIds = useMemo(() => {
    if (!day?.segments?.length) return [];
    return day.segments.map((s) => s.posteId);
  }, [day]);

  const { posteNameById } = usePosteNamesById(segmentPosteIds);

  const isWorking = dayType === "working";
  const canSave = !!day && (!isWorking || trancheId !== null);

  const uiDisabled = busy || loading; // loading bloque tout ; validating = info

  const rhCounts = useMemo(() => {
    let error = 0,
      warning = 0,
      info = 0;
    for (const v of rhViolations) {
      if (v.severity === "error") error++;
      else if (v.severity === "warning") warning++;
      else info++;
    }
    return { error, warning, info, total: rhViolations.length };
  }, [rhViolations]);

  const rhSorted = useMemo(() => {
    const rank = (s: string) => (s === "error" ? 0 : s === "warning" ? 1 : 2);
    return rhViolations
      .slice()
      .sort((a, b) => rank(a.severity) - rank(b.severity));
  }, [rhViolations]);

  const rhMain = useMemo(
    () =>
      rhSorted.filter(
        (v) => v.severity === "error" || v.severity === "warning",
      ),
    [rhSorted],
  );

  const rhInfos = useMemo(
    () => rhSorted.filter((v) => v.severity === "info"),
    [rhSorted],
  );

  const [showInfos, setShowInfos] = useState(false);

  function handleCancel() {
    if (!day) return;
    setDayType(day.day_type ?? "rest");
    setDescription(day.description ?? "");
    setTrancheId(day.tranche_id ?? null);
  }

  async function handleSave() {
    if (!day) return;

    await onSave({
      dayDate: day.day_date,
      day_type: dayType,
      description: description.trim() ? description.trim() : null,
      tranche_id: isWorking ? trancheId : null,
    });

    setCoverageRefreshKey((x) => x + 1);
  }

  async function handleDelete() {
    if (!day) return;
    await onDelete(day.day_date);
    onClose();
  }

  const headerSummary = useMemo(() => {
    if (!day) return null;

    const hasSegments = day.segments?.length > 0;

    if (dayType === "working" && hasSegments) {
      const first = day.segments[0];
      const start = first.start.slice(0, 5);
      const end = first.end.slice(0, 5);
      const poste =
        posteNameById.get(first.posteId) ?? `Poste #${first.posteId}`;
      return (
        <span className="truncate text-xs text-muted-foreground">
          {poste} • {start}–{end}
        </span>
      );
    }

    if (description.trim()) {
      return (
        <span className="truncate text-xs text-muted-foreground">
          {description.trim()}
        </span>
      );
    }

    return (
      <span className="truncate text-xs text-muted-foreground">
        Planning du jour
      </span>
    );
  }, [day, dayType, description, posteNameById]);

  const descriptionId = useMemo(() => "agent-day-description", []);

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      bodyClassName="p-4"
      title={
        <span className="flex min-w-0 items-center gap-2">
          <span className="truncate">{dateLabel}</span>
          {day ? <DayTypeBadge dayType={dayType} /> : null}
        </span>
      }
      description={headerSummary}
    >
      <div className="space-y-4">
        {day ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={uiDisabled}
              >
                Annuler
              </Button>

              <Button
                size="sm"
                onClick={handleSave}
                disabled={uiDisabled || !canSave}
              >
                Enregistrer
              </Button>

              <div className="flex-1" />

              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                disabled={uiDisabled}
              >
                Supprimer
              </Button>
            </div>

            {loading ? (
              <p className="text-xs text-muted-foreground">Chargement…</p>
            ) : validating ? (
              <p className="text-xs text-muted-foreground">Mise à jour…</p>
            ) : null}

            {loadError ? (
              <p className="text-xs text-destructive">
                Impossible de charger le planning. {loadError}
              </p>
            ) : null}

            {actionError ? (
              <p className="text-xs text-destructive">{actionError}</p>
            ) : null}
          </div>
        ) : null}

        <div className={cn("rounded-xl border bg-card p-3", "space-y-4")}>
          {!day ? (
            <EmptyBox>Aucun jour sélectionné.</EmptyBox>
          ) : (
            <>
              {/* si DayTypeSelect supporte disabled, passe-le ; sinon bloque via wrapper plus tard */}
              <DayTypeSelect
                value={dayType}
                onValueChange={setDayType}
                disabled={uiDisabled}
              />

              {isWorking ? (
                <div className="space-y-2">
                  <QualifiedTrancheSelect
                    agentId={agentId}
                    value={trancheId}
                    dateISO={day.day_date}
                    onChange={setTrancheId}
                    label="Tranche"
                    refreshKey={coverageRefreshKey}
                    disabled={uiDisabled}
                  />

                  {trancheId === null ? (
                    <p className="text-xs text-destructive">
                      Tranche obligatoire pour “working”.
                    </p>
                  ) : null}
                </div>
              ) : null}

              <div className="space-y-2">
                <Label
                  htmlFor={descriptionId}
                  className="text-xs text-muted-foreground"
                >
                  Description
                </Label>
                <Input
                  id={descriptionId}
                  placeholder="Optionnel"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={uiDisabled}
                />
              </div>
            </>
          )}
        </div>

        {day ? (
          <div className="rounded-xl border bg-card p-3 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-semibold text-foreground">
                Contrôle RH
              </div>

              <div className="flex items-center gap-2">
                <Badge
                  variant={rhCounts.error > 0 ? "destructive" : "outline"}
                  className="h-5 rounded-full px-2 py-0 text-[10px]"
                >
                  {rhCounts.error} erreur(s)
                </Badge>
                <Badge
                  variant={rhCounts.warning > 0 ? "secondary" : "outline"}
                  className="h-5 rounded-full px-2 py-0 text-[10px]"
                >
                  {rhCounts.warning} alerte(s)
                </Badge>
                <Badge
                  variant="outline"
                  className="h-5 rounded-full px-2 py-0 text-[10px]"
                >
                  {rhCounts.info} info(s)
                </Badge>
              </div>
            </div>

            {rhCounts.total === 0 ? (
              <p className="text-xs text-muted-foreground">
                Aucune violation RH détectée pour ce jour.
              </p>
            ) : (
              <div className="space-y-2">
                {/* Errors + warnings par défaut */}
                {rhMain.length > 0 ? (
                  <div className="space-y-2">
                    {rhMain.slice(0, 5).map((v, i) => (
                      <div
                        key={`${v.code}-${i}`}
                        className="rounded-lg border p-2"
                      >
                        <div className="flex items-start gap-2">
                          <Badge
                            variant={
                              v.severity === "error"
                                ? "destructive"
                                : "secondary"
                            }
                            className="h-5 rounded-full px-2 py-0 text-[10px]"
                          >
                            {v.severity.toUpperCase()}
                          </Badge>

                          <div className="min-w-0">
                            <div className="text-sm leading-snug">
                              {v.message}
                            </div>
                            <div className="text-[11px] text-muted-foreground">
                              {(v.rule && v.rule.trim().length > 0
                                ? v.rule
                                : v.code) ?? ""}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {rhMain.length > 5 ? (
                      <p className="text-[11px] text-muted-foreground">
                        +{rhMain.length - 5} autre(s) alerte(s) (voir “Contrôle
                        RH” dans le header).
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Pas d’erreur/alerte RH bloquante sur ce jour.
                  </p>
                )}

                {/* Infos (cachées par défaut) */}
                {rhInfos.length > 0 ? (
                  <div className="pt-1">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowInfos((v) => !v)}
                      className="px-2"
                    >
                      {showInfos
                        ? "Masquer les infos"
                        : `Afficher les infos (${rhInfos.length})`}
                    </Button>

                    {showInfos ? (
                      <div className="mt-2 space-y-2">
                        {rhInfos.slice(0, 5).map((v, i) => (
                          <div
                            key={`${v.code}-info-${i}`}
                            className="rounded-lg border p-2"
                          >
                            <div className="flex items-start gap-2">
                              <Badge
                                variant="outline"
                                className="h-5 rounded-full px-2 py-0 text-[10px]"
                              >
                                INFO
                              </Badge>

                              <div className="min-w-0">
                                <div className="text-sm leading-snug">
                                  {v.message}
                                </div>
                                <div className="text-[11px] text-muted-foreground">
                                  {(v.rule && v.rule.trim().length > 0
                                    ? v.rule
                                    : v.code) ?? ""}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}

                        {rhInfos.length > 5 ? (
                          <p className="text-[11px] text-muted-foreground">
                            +{rhInfos.length - 5} autre(s) info(s) (voir
                            “Contrôle RH” dans le header).
                          </p>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        ) : null}

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-foreground">Aperçu</div>

            {day && day.segments.length > 0 ? (
              <Badge variant="outline" className="tabular-nums">
                {day.segments[0].start.slice(0, 5)}–
                {day.segments[0].end.slice(0, 5)}
              </Badge>
            ) : null}
          </div>

          <div className="rounded-xl border bg-card p-3">
            {day ? (
              <AgentDayGantt
                segments={day.segments}
                dayStart="00:00:00"
                dayEnd="23:59:00"
              />
            ) : (
              <EmptyBox>Aucun jour sélectionné.</EmptyBox>
            )}
          </div>
        </div>
      </div>
    </PlanningSheetShell>
  );
}
