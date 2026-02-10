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
import { DayTypeSelect } from "@/components/planning/DayTypeSelect";
import { cn } from "@/lib/utils";
import { usePosteNamesById } from "@/features/postes/hooks/usePosteNamesById";

export type AgentDaySheetSavePayload = {
  dayDate: string;
  day_type: string;
  description: string | null;
  tranche_id: number | null;
};

export function AgentDaySheetView({
  open,
  onClose,
  day,
  agentId,
  onSave,
  onDelete,
}: {
  open: boolean;
  onClose: () => void;
  day: AgentDayVm | null;
  agentId: number;
  onSave: (payload: AgentDaySheetSavePayload) => Promise<void>;
  onDelete: (dayDate: string) => Promise<void>;
}) {
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
      const poste = posteNameById.get(first.posteId) ?? `Poste #${first.posteId}`;
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

        <div className={cn("rounded-xl border bg-card p-3", "space-y-4")}>
          {!day ? (
            <EmptyBox>Aucun jour sélectionné.</EmptyBox>
          ) : (
            <>
              <DayTypeSelect value={dayType} onValueChange={setDayType} />

              {isWorking ? (
                <div className="space-y-2">
                  <QualifiedTrancheSelect
                    agentId={agentId}
                    value={trancheId}
                    dateISO={day.day_date}
                    onChange={setTrancheId}
                    label="Tranche"
                    refreshKey={coverageRefreshKey}
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
                />
              </div>
            </>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-foreground">Aperçu</div>

            {day && day.segments.length > 0 ? (
              <Badge variant="outline" className="tabular-nums">
                {day.segments[0].start.slice(0, 5)}–{day.segments[0].end.slice(0, 5)}
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
