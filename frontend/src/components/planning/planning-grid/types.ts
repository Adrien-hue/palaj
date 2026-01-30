import type { ReactNode } from "react";

export type WeekStartsOn = 0 | 1;

export type PlanningGridCellRenderArgs<TDay> = {
  date: string; // ISO YYYY-MM-DD
  day: TDay;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  isOutsideRange?: boolean;
  onSelect: () => void;
};

export type PlanningGridDetailsRenderArgs<TDay> = {
  open: boolean;
  selectedDate: string | null;
  selectedDay: TDay | null;
  close: () => void;
  setSelectedDate: (d: string | null) => void;
};

export type RangeMode = {
  mode: "range";
  startDate: string; // requested
  endDate: string; // requested
  anchorMonth?: never;
  alignToWeeks?: boolean;
};

export type MonthMode = {
  mode: "month";
  anchorMonth: string; // any day in month
  startDate?: string;
  endDate?: string;
};

export type CommonProps<TDay> = {
  getDay: (isoDate: string) => TDay | undefined;
  getDayDate: (day: TDay) => string;

  renderCell: (args: PlanningGridCellRenderArgs<TDay>) => ReactNode;
  renderDetails: (args: PlanningGridDetailsRenderArgs<TDay>) => ReactNode;

  renderEmptyCell?: (args: {
    date: string;
    isOutsideMonth: boolean;
    isOutsideRange?: boolean;
  }) => ReactNode;

  closeOnEscape?: boolean;
  gridLabel?: string;

  weekStartsOn?: WeekStartsOn;

  maxHeight?: number | string;
  scrollAreaClassName?: string;

  selectedDate?: string | null;
  onSelectedDateChange?: (d: string | null) => void;
};

export type PlanningGridBaseProps<TDay> = (RangeMode | MonthMode) & CommonProps<TDay>;

export type DayHeaderLabel = {
  short: string;
  full: string;
};

export type DisplayInfo =
  | {
      mode: "range";
      requestedStart: string;
      requestedEnd: string;
      displayStart: string;
      displayEnd: string;
      anchorMonth: null;
    }
  | {
      mode: "month";
      requestedStart: null;
      requestedEnd: null;
      displayStart: string;
      displayEnd: string;
      anchorMonth: string;
    };
