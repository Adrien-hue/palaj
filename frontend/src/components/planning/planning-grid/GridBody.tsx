import { cn } from "@/lib/utils";
import type { ReactNode } from "react";
import type { PlanningGridCellRenderArgs } from "./types";
import type { FocusBindings } from "./useRovingGridFocus";

export function GridBody<TDay>({
  allDates,
  gridLabel,

  getDay,
  renderCell,
  renderEmptyCell,

  isOutsideMonthFor,
  isOutsideRangeFor,

  isSelectedDate,
  isInSelectedWeek,

  onSelectDate,

  getFocusBindings,

  minCellHeight = 72,
}: {
  allDates: string[];
  gridLabel: string;

  getDay: (iso: string) => TDay | undefined;

  renderCell: (args: PlanningGridCellRenderArgs<TDay>) => ReactNode;
  renderEmptyCell?: (args: {
    date: string;
    isOutsideMonth: boolean;
    isOutsideRange?: boolean;
  }) => ReactNode;

  isOutsideMonthFor: (date: string) => boolean;
  isOutsideRangeFor: (date: string) => boolean;

  isSelectedDate: (date: string) => boolean;
  isInSelectedWeek: (date: string) => boolean;

  onSelectDate: (date: string) => void;

  getFocusBindings: (date: string) => FocusBindings;

  minCellHeight?: number;
}) {
  return (
    <div
      className="grid grid-cols-7 gap-2 px-2 py-2 sm:gap-3"
      role="grid"
      aria-label={gridLabel}
    >
      {allDates.map((date) => {
        const day = getDay(date);

        const isOutsideMonth = isOutsideMonthFor(date);
        const isOutsideRange = isOutsideRangeFor(date);

        const isSelected = isSelectedDate(date);
        const isWeek = isInSelectedWeek(date);

        const disabled = isOutsideRange || !day;

        if (!day) {
          return (
            <div key={date} role="gridcell" aria-disabled="true">
              {renderEmptyCell ? (
                renderEmptyCell({ date, isOutsideMonth, isOutsideRange })
              ) : (
                <div
                  className={cn(
                    "rounded-xl border bg-muted/30",
                    isOutsideMonth && "opacity-70",
                    isOutsideRange && "border-dashed bg-muted/20 opacity-50"
                  )}
                  style={{ minHeight: minCellHeight }}
                />
              )}
            </div>
          );
        }

        const focus = getFocusBindings(date);

        return (
          <div
            key={date}
            role="gridcell"
            aria-disabled={disabled ? "true" : undefined}
            tabIndex={focus.tabIndex}
            ref={focus.ref}
            onFocus={focus.onFocus}
            onKeyDown={focus.onKeyDown}
            className={cn(
              "rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              isOutsideMonth && "opacity-80",
              isOutsideRange && "pointer-events-none opacity-60"
            )}
          >
            {renderCell({
              date,
              day,
              isOutsideMonth,
              isSelected,
              isInSelectedWeek: isWeek,
              isOutsideRange,
              onSelect: () => {
                if (disabled) return;
                onSelectDate(date);
              },
            })}
          </div>
        );
      })}
    </div>
  );
}
