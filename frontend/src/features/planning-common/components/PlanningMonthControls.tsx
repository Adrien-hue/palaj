"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { usePlanningMonthParam } from "@/features/planning-common/hooks/usePlanningMonthParam";

const MONTHS_FR = [
  "Janvier","Février","Mars","Avril","Mai","Juin",
  "Juillet","Août","Septembre","Octobre","Novembre","Décembre",
];

export function PlanningMonthControls({
  yearsRange = 5,
  navMode = "push",
}: {
  yearsRange?: number;
  navMode?: "push" | "replace";
}) {
  const { anchor, year, monthIndex, setAnchor, stepMonth } = usePlanningMonthParam();

  const years = Array.from({ length: yearsRange * 2 + 1 }, (_, i) => year - yearsRange + i);

  return (
    <TooltipProvider>
      <div className="flex flex-wrap items-center justify-end gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              onClick={() => stepMonth(-1, navMode)}
              aria-label="Mois précédent"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Mois précédent</TooltipContent>
        </Tooltip>

        <Select
          value={String(monthIndex)}
          onValueChange={(v) => {
            const mi = Number(v);
            setAnchor(`${year}-${String(mi + 1).padStart(2, "0")}-01`, navMode);
          }}
        >
          <SelectTrigger className="h-9 w-[150px]">
            <SelectValue aria-label="Sélection du mois" />
          </SelectTrigger>
          <SelectContent>
            {MONTHS_FR.map((m, i) => (
              <SelectItem key={m} value={String(i)}>
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={String(year)}
          onValueChange={(v) => {
            const y = Number(v);
            setAnchor(`${y}-${String(monthIndex + 1).padStart(2, "0")}-01`, navMode);
          }}
        >
          <SelectTrigger className="h-9 w-[110px]">
            <SelectValue aria-label="Sélection de l'année" />
          </SelectTrigger>
          <SelectContent>
            {years.map((y) => (
              <SelectItem key={y} value={String(y)}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              onClick={() => stepMonth(1, navMode)}
              aria-label="Mois suivant"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Mois suivant</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}
