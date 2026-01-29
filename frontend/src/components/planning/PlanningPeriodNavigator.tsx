"use client";

import * as React from "react";
import { fr } from "date-fns/locale";
import { format, startOfMonth, endOfMonth, addDays } from "date-fns";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
} from "lucide-react";

import type {
  PlanningPeriod,
  MonthPeriod,
  RangePeriod,
} from "@/features/planning-common/period/period.types";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";

type Preset = 7 | 14 | 28;

export type PlanningPeriodNavigatorProps = {
  value: PlanningPeriod;
  onChange: (p: PlanningPeriod) => void;
  onPrev: () => void;
  onNext: () => void;

  disabled?: boolean;
  presets?: Preset[];
  className?: string;
};

function isMonthPeriod(p: PlanningPeriod): p is MonthPeriod {
  return p.kind === "month";
}

function isRangePeriod(p: PlanningPeriod): p is RangePeriod {
  return p.kind === "range";
}

function periodLabel(p: PlanningPeriod) {
  if (p.kind === "month") {
    return format(p.month, "LLLL yyyy", { locale: fr });
  }

  const sameMonth =
    p.start.getMonth() === p.end.getMonth() &&
    p.start.getFullYear() === p.end.getFullYear();

  if (sameMonth) {
    return `${format(p.start, "d", { locale: fr })}–${format(
      p.end,
      "d LLLL yyyy",
      { locale: fr },
    )}`;
  }

  return `${format(p.start, "d LLL", { locale: fr })}–${format(
    p.end,
    "d LLL yyyy",
    { locale: fr },
  )}`;
}

export function PlanningPeriodNavigator({
  value,
  onChange,
  onPrev,
  onNext,
  disabled,
  presets = [7, 14, 28],
  className,
}: PlanningPeriodNavigatorProps) {
  const [open, setOpen] = React.useState(false);
  const mode = value.kind;

  const rangeBaseMonth = React.useMemo(() => {
    const base = value.kind === "range" ? value.start : value.month;
    return startOfMonth(base);
  }, [value]);

  const switchToMonth = (d: Date) => {
    onChange({ kind: "month", month: startOfMonth(d) });
    setOpen(false);
  };

  const switchToRange = (start: Date, days: number) => {
    const s = new Date(start);
    s.setHours(0, 0, 0, 0);
    const e = addDays(s, days - 1);
    onChange({ kind: "range", start: s, end: e });
    setOpen(false);
  };

  return (
    <div className={className}>
      <div className="inline-flex items-stretch rounded-md border border-border bg-background shadow-sm">
        <Button
          variant="ghost"
          size="icon"
          onClick={onPrev}
          disabled={disabled}
          aria-label="Période précédente"
          className="h-9 w-9 rounded-none rounded-l-md"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <Separator orientation="vertical" className="h-9 opacity-60" />

        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              disabled={disabled}
              className="h-9 min-w-[240px] rounded-none justify-between px-3"
            >
              <span className="truncate capitalize">{periodLabel(value)}</span>

              <span className="inline-flex items-center gap-2">
                <Badge
                  variant={mode === "month" ? "outline" : "secondary"}
                  className="rounded-full"
                >
                  {mode === "month" ? "Mois" : "Plage"}
                </Badge>
                <CalendarIcon className="h-4 w-4 opacity-70" />
              </span>
            </Button>
          </PopoverTrigger>

          <PopoverContent className="w-[360px] p-3" align="start">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Période</div>
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant={mode === "month" ? "default" : "outline"}
                  onClick={() => {
                    const base = isMonthPeriod(value)
                      ? value.month
                      : value.start;
                    onChange({ kind: "month", month: startOfMonth(base) });
                  }}
                >
                  Mois
                </Button>

                <Button
                  size="sm"
                  variant={mode === "range" ? "default" : "outline"}
                  onClick={() => {
                    const base = isRangePeriod(value)
                      ? value.start
                      : value.month;
                    switchToRange(startOfMonth(base), 14);
                  }}
                >
                  Plage
                </Button>
              </div>
            </div>

            <Separator className="my-3 opacity-50" />

            {mode === "month" ? (
              <Calendar
                mode="single"
                selected={isMonthPeriod(value) ? value.month : undefined}
                onSelect={(d) => d && switchToMonth(d)}
                captionLayout="dropdown"
                fromYear={2020}
                toYear={2035}
                locale={fr}
              />
            ) : (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {presets.map((p) => (
                    <Button
                      key={p}
                      size="sm"
                      variant="outline"
                      onClick={() => switchToRange(rangeBaseMonth, p)}
                    >
                      {p} jours
                    </Button>
                  ))}

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      onChange({
                        kind: "range",
                        start: rangeBaseMonth,
                        end: endOfMonth(rangeBaseMonth),
                      });
                      setOpen(false);
                    }}
                  >
                    Mois complet
                  </Button>
                </div>

                <Calendar
                  mode="range"
                  selected={
                    isRangePeriod(value)
                      ? { from: value.start, to: value.end }
                      : undefined
                  }
                  onSelect={(r) => {
                    if (!r?.from) return;
                    const start = new Date(r.from);
                    const end = new Date(r.to ?? r.from);
                    start.setHours(0, 0, 0, 0);
                    end.setHours(0, 0, 0, 0);
                    onChange({ kind: "range", start, end });
                  }}
                  numberOfMonths={1}
                  locale={fr}
                />

                <div className="text-xs text-muted-foreground">
                  Les boutons ← → déplacent la plage par sa durée.
                </div>
              </div>
            )}
          </PopoverContent>
        </Popover>

        <Separator orientation="vertical" className="h-9 opacity-60" />

        <Button
          variant="ghost"
          size="icon"
          onClick={onNext}
          disabled={disabled}
          aria-label="Période suivante"
          className="h-9 w-9 rounded-none rounded-r-md"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
