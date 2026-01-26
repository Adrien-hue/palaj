"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import type { QualificationOption } from "./types";

export default function AddQualificationPanel({
  entityLabel,
  disabled,
  optLoading,
  availableOptions,
  addRelatedId,
  addDate,
  onChangeRelatedId,
  onChangeDate,
  onCancel,
  onSubmit,
}: {
  entityLabel: string;
  disabled: boolean;
  optLoading: boolean;
  availableOptions: QualificationOption[];
  addRelatedId: number | "";
  addDate: string;
  onChangeRelatedId: (v: number | "") => void;
  onChangeDate: (v: string) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const NONE = "__none__";

  const canSubmit =
    !disabled && addRelatedId !== "" && !!addDate && availableOptions.length > 0;

  const selectValue =
    addRelatedId === "" ? NONE : String(addRelatedId);

  return (
    <div className={cn("rounded-xl border bg-muted/30 p-4")}>
      <div className="text-sm font-semibold text-foreground">
        Ajouter une qualification
      </div>

      <div className="mt-1 text-xs text-muted-foreground">
        {availableOptions.length === 0
          ? `Aucun ${entityLabel.toLowerCase()} disponible à ajouter.`
          : `${availableOptions.length} disponible(s)`}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            {entityLabel}
          </div>

          <Select
            value={selectValue}
            onValueChange={(v) => {
              if (v === NONE) onChangeRelatedId("");
              else onChangeRelatedId(Number(v));
            }}
            disabled={disabled || optLoading || availableOptions.length === 0}
          >
            <SelectTrigger>
              <SelectValue placeholder="Sélectionner…" />
            </SelectTrigger>

            <SelectContent>
              {/* Radix interdit value="" */}
              <SelectItem value={NONE}>— Sélectionner —</SelectItem>

              {availableOptions.map((o) => (
                <SelectItem key={o.id} value={String(o.id)}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            Date de qualification
          </div>

          <Input
            type="date"
            value={addDate}
            onChange={(e) => onChangeDate(e.target.value)}
            disabled={disabled}
          />
        </div>
      </div>

      <div className="mt-4 flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onCancel}
          disabled={disabled}
        >
          Annuler
        </Button>

        <Button
          type="button"
          size="sm"
          onClick={onSubmit}
          disabled={!canSubmit}
        >
          Ajouter
        </Button>
      </div>

      {optLoading ? (
        <div className="mt-2 text-xs text-muted-foreground">Chargement…</div>
      ) : null}
    </div>
  );
}
