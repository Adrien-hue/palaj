"use client";

import { useMemo, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import type { PlanningGridBaseProps } from "./planning-grid/types";
import { usePlanningGridDates } from "./planning-grid/usePlanningGridDates";
import { useRovingGridFocus } from "./planning-grid/useRovingGridFocus";
import { GridHeader } from "./planning-grid/GridHeader";
import { GridBody } from "./planning-grid/GridBody";
import { isoWeekRangeFrom } from "@/utils/date.format";

type WeekRange = { start: string; end: string };

export function PlanningGridBase<TDay>(props: PlanningGridBaseProps<TDay>) {
  const {
    getDay,
    getDayDate,
    renderCell,
    renderDetails,
    renderEmptyCell,

    closeOnEscape = true,
    gridLabel = "Planning",

    selectedDate: controlledSelectedDate,
    onSelectedDateChange,

    maxHeight,
    scrollAreaClassName,
  } = props;

  // Controlled/uncontrolled selection
  const [uncontrolledSelectedDate, setUncontrolledSelectedDate] = useState<
    string | null
  >(null);
  const selectedDate = controlledSelectedDate ?? uncontrolledSelectedDate;

  const setSelectedDate = (d: string | null) => {
    onSelectedDateChange?.(d);
    if (controlledSelectedDate === undefined) setUncontrolledSelectedDate(d);
  };

  const {
    display,
    allDates,
    daysHeader,
    isOutsideMonthFor,
    isOutsideRangeFor,
  } = usePlanningGridDates(props);

  const selectedDay = selectedDate ? (getDay(selectedDate) ?? null) : null;

  const selectedWeek = useMemo<WeekRange | null>(() => {
    if (!selectedDay) return null;
    return isoWeekRangeFrom(getDayDate(selectedDay));
  }, [selectedDay, getDayDate]);

  const isSelectedDate = (d: string) => selectedDate === d;
  const isInSelectedWeek = (d: string) => {
    if (!selectedWeek) return false;
    return d >= selectedWeek.start && d <= selectedWeek.end;
  };

  const isDisabled = (d: string) => isOutsideRangeFor(d) || !getDay(d);

  const focus = useRovingGridFocus({
    allDates,
    selectedDate,
    setSelectedDate,
    isDisabled,
    closeOnEscape,
  });

  // Scroll area height
  const scrollStyle =
    typeof maxHeight === "string"
      ? { height: maxHeight }
      : typeof maxHeight === "number"
        ? { height: `${maxHeight}px` }
        : undefined;

  return (
    <Card className="p-0 overflow-hidden">
      <CardContent className="p-0">
        <ScrollArea
          className={cn(
            "w-full",
            maxHeight == null && "h-[55vh]",
            scrollAreaClassName,
          )}
          style={scrollStyle}
        >
          <div className="relative">
            <GridHeader days={daysHeader} />
            <GridBody<TDay>
              allDates={allDates}
              gridLabel={gridLabel}
              getDay={getDay}
              renderCell={renderCell}
              renderEmptyCell={renderEmptyCell}
              isOutsideMonthFor={isOutsideMonthFor}
              isOutsideRangeFor={isOutsideRangeFor}
              isSelectedDate={isSelectedDate}
              isInSelectedWeek={isInSelectedWeek}
              onSelectDate={(date) => {
                focus.rememberActiveElement();
                focus.setFocusedDate(date);
                setSelectedDate(date);
              }}
              getFocusBindings={focus.getFocusBindings}
            />
          </div>
        </ScrollArea>

        {renderDetails({
          open: !!selectedDay,
          selectedDate,
          selectedDay,
          close: () => setSelectedDate(null),
          setSelectedDate,
        })}
      </CardContent>
    </Card>
  );
}
