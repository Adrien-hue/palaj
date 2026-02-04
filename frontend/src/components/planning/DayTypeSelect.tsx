"use client";

import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

import {
  DAY_TYPE_OPTIONS,
  dayTypeLabel,
} from "@/components/planning/dayTypes";
import { cn } from "@/lib/utils";

export function DayTypeSelect({
  value,
  onValueChange,
  label = "Type de journée",
  placeholder = "Choisir un type",
  disabled,
  className,
}: {
  value: string;
  onValueChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}) {
  const id = React.useId();

  return (
    <div className={cn("space-y-1", className)}>
      {label ? (
        <Label htmlFor={id} className="text-xs text-muted-foreground">
          {label}
        </Label>
      ) : null}

      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder={placeholder}>
            {value ? dayTypeLabel(value) : null}
          </SelectValue>
        </SelectTrigger>

        <SelectContent>
          {DAY_TYPE_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
