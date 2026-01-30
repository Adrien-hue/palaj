import { useMemo } from "react";
import { endOfWeek, format as dfFormat, parseISO, startOfMonth, startOfWeek, endOfMonth } from "date-fns";

import { buildDaysRange, isInSameMonth, isoWeekRangeFrom, monthGridRangeFrom } from "@/utils/date.format";
import { getDaysHeader } from "./constants";
import type { DisplayInfo, PlanningGridBaseProps, WeekStartsOn } from "./types";

function weekRangeFrom(iso: string, weekStartsOn: WeekStartsOn): { start: string; end: string } {
  if (weekStartsOn === 1) return isoWeekRangeFrom(iso);

  const d = parseISO(iso);
  const start = startOfWeek(d, { weekStartsOn: 0 });
  const end = endOfWeek(d, { weekStartsOn: 0 });
  return { start: dfFormat(start, "yyyy-MM-dd"), end: dfFormat(end, "yyyy-MM-dd") };
}

export function usePlanningGridDates<TDay>(props: PlanningGridBaseProps<TDay>) {
  const weekStartsOn = props.weekStartsOn ?? 1;

  const display: DisplayInfo = useMemo(() => {
    if (props.mode === "range") {
      const requestedStart = props.startDate;
      const requestedEnd = props.endDate;
      const align = props.alignToWeeks ?? true;

      if (!align) {
        return {
          mode: "range",
          requestedStart,
          requestedEnd,
          displayStart: requestedStart,
          displayEnd: requestedEnd,
          anchorMonth: null,
        };
      }

      const startWeek = weekRangeFrom(requestedStart, weekStartsOn);
      const endWeek = weekRangeFrom(requestedEnd, weekStartsOn);

      return {
        mode: "range",
        requestedStart,
        requestedEnd,
        displayStart: startWeek.start,
        displayEnd: endWeek.end,
        anchorMonth: null,
      };
    }

    // month mode
    if (weekStartsOn === 1) {
      const computed = monthGridRangeFrom(props.anchorMonth);
      return {
        mode: "month",
        requestedStart: null,
        requestedEnd: null,
        displayStart: props.startDate ?? computed.start,
        displayEnd: props.endDate ?? computed.end,
        anchorMonth: props.anchorMonth,
      };
    }

    // month mode, Sunday-first
    const anchor = parseISO(props.anchorMonth);
    const first = startOfMonth(anchor);
    const last = endOfMonth(anchor);
    const start = startOfWeek(first, { weekStartsOn: 0 });
    const end = endOfWeek(last, { weekStartsOn: 0 });

    return {
      mode: "month",
      requestedStart: null,
      requestedEnd: null,
      displayStart: dfFormat(start, "yyyy-MM-dd"),
      displayEnd: dfFormat(end, "yyyy-MM-dd"),
      anchorMonth: props.anchorMonth,
    };
  }, [
    props.mode,
    weekStartsOn,
    props.mode === "range" ? props.startDate : null,
    props.mode === "range" ? props.endDate : null,
    props.mode === "range" ? props.alignToWeeks : null,
    props.mode === "month" ? props.anchorMonth : null,
    props.mode === "month" ? props.startDate : null,
    props.mode === "month" ? props.endDate : null,
  ]);

  const allDates = useMemo(() => buildDaysRange(display.displayStart, display.displayEnd), [
    display.displayStart,
    display.displayEnd,
  ]);

  const daysHeader = useMemo(() => getDaysHeader(weekStartsOn), [weekStartsOn]);

  const isOutsideMonthFor = (date: string) => {
    if (props.mode !== "month") return false;
    return !isInSameMonth(date, props.anchorMonth);
  };

  const isOutsideRangeFor = (date: string) => {
    if (display.mode !== "range") return false;
    return date < display.requestedStart || date > display.requestedEnd;
  };

  return { weekStartsOn, display, allDates, daysHeader, isOutsideMonthFor, isOutsideRangeFor };
}
