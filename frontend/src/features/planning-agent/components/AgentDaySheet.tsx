"use client";

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
import { useAgentPlanningEdit } from "@/features/planning-agent/hooks/useAgentPlanningEdit";
import type { AgentPlanningKey } from "@/features/planning-agent/hooks/agentPlanning.key";

import { DayTypeSelect } from "@/components/planning/DayTypeSelect";
import { cn } from "@/lib/utils";

export function AgentDaySheet({
  open,
  onClose,
  selectedDay,
  posteNameById,
  agentId,
  planningKey,
}: {
  open: boolean;
  onClose: () => void;
  selectedDay: AgentDayVm | null;
  posteNameById: Map<number, string>;
  agentId: number;
  planningKey: AgentPlanningKey | null;
}) {
  const dateLabel = selectedDay ? formatDateFR(selectedDay.day_date) : "Jour";
  const { saveDay, removeDay } = useAgentPlanningEdit(agentId, planningKey);

  // -----
  // Form state
  // -----
  const [dayType, setDayType] = useState<string>("rest");
  const [description, setDescription] = useState<string>("");
  const [trancheId, setTrancheId] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedDay) return;
    setDayType(selectedDay.day_type ?? "rest");
    setDescription(selectedDay.description ?? "");
    setTrancheId(selectedDay.tranche_id ?? null);
  }, [selectedDay?.day_date]);

  const isWorking = dayType === "working";
  const canSave = !!selectedDay && (!isWorking || trancheId !== null);

  function handleCancel() {
    if (!selectedDay) return;
    setDayType(selectedDay.day_type ?? "rest");
    setDescription(selectedDay.description ?? "");
    setTrancheId(selectedDay.tranche_id ?? null);
  }

  async function handleSave() {
    if (!selectedDay) return;

    await saveDay({
      dayDate: selectedDay.day_date,
      day_type: dayType,
      description: description.trim() ? description.trim() : null,
      tranche_id: isWorking ? trancheId : null,
    });
  }

  async function handleDelete() {
    if (!selectedDay) return;
    await removeDay(selectedDay.day_date);
    onClose();
  }

  const headerSummary = useMemo(() => {
    if (!selectedDay) return null;

    const hasSegments = selectedDay.segments?.length > 0;

    if (dayType === "working" && hasSegments) {
      const first = selectedDay.segments[0];
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

    if (dayType === "working" && !hasSegments) {
      return (
        <span className="truncate text-xs text-muted-foreground">
          À disposition (ZCOT)
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
  }, [selectedDay, dayType, description, posteNameById]);

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
          {selectedDay ? <DayTypeBadge dayType={dayType} /> : null}
        </span>
      }
      description={headerSummary}
    >
      <div className="space-y-4">
        {/* Actions */}
        {selectedDay ? (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleCancel}>
              Annuler
            </Button>

            <Button size="sm" onClick={handleSave} disabled={!canSave}>
              Enregistrer
            </Button>

            <div className="flex-1" />

            <Button variant="destructive" size="sm" onClick={handleDelete}>
              Supprimer
            </Button>
          </div>
        ) : null}

        {/* Form compact */}
        <div className={cn("rounded-xl border bg-card p-3", "space-y-4")}>
          {!selectedDay ? (
            <EmptyBox>Aucun jour sélectionné.</EmptyBox>
          ) : (
            <>
              {/* DayTypeSelect a déjà son Label intégré */}
              <DayTypeSelect value={dayType} onValueChange={setDayType} />

              {isWorking ? (
                <div className="space-y-2">
                  <QualifiedTrancheSelect
                    agentId={agentId}
                    value={trancheId}
                    onChange={setTrancheId}
                    posteNameById={posteNameById}
                    label="Tranche"
                  />

                  {trancheId === null ? (
                    <p className="text-xs text-destructive">
                      Tranche obligatoire pour “working”.
                    </p>
                  ) : null}
                </div>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor={descriptionId} className="text-xs text-muted-foreground">
                  Description
                </Label>
                <Input
                  id={descriptionId}
                  placeholder="Optionnel"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </>
          )}
        </div>

        {/* Aperçu / Timeline */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-foreground">Aperçu</div>

            {selectedDay && selectedDay.segments.length > 0 ? (
              <Badge variant="outline" className="tabular-nums">
                {selectedDay.segments[0].start.slice(0, 5)}–
                {selectedDay.segments[0].end.slice(0, 5)}
              </Badge>
            ) : null}
          </div>

          <div className="rounded-xl border bg-card p-3">
            {selectedDay ? (
              <AgentDayGantt
                segments={selectedDay.segments}
                posteNameById={posteNameById}
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
