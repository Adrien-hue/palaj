import { addDaysISO } from "@/utils/date.format";
import { timeToMinutes } from "@/utils/time.format";

export type OvernightSplitArgs<TInput> = {
  dayDate: string;
  input: TInput;
  start: string; // HH:MM:SS
  end: string;   // HH:MM:SS
  endOfDay?: string;   // default "23:59:00"
  startOfDay?: string; // default "00:00:00"
};

export type OvernightSplitPart<TSeg> = { day_date: string; seg: TSeg };

export function splitOvernight<TInput, TSeg>(
  args: OvernightSplitArgs<TInput>,
  makeSeg: (p: {
    day_date: string;
    start: string;
    end: string;
    continuesPrev: boolean;
    continuesNext: boolean;
    input: TInput;
  }) => TSeg
): OvernightSplitPart<TSeg>[] {
  const { dayDate, input } = args;
  const startOfDay = args.startOfDay ?? "00:00:00";
  const endOfDay = args.endOfDay ?? "23:59:00";

  const startMin = timeToMinutes(args.start);
  const endMin = timeToMinutes(args.end);

  // Same day
  if (endMin >= startMin) {
    return [
      {
        day_date: dayDate,
        seg: makeSeg({
          day_date: dayDate,
          start: args.start,
          end: args.end,
          continuesPrev: false,
          continuesNext: false,
          input,
        }),
      },
    ];
  }

  // Overnight split
  const nextDay = addDaysISO(dayDate, 1);

  return [
    {
      day_date: dayDate,
      seg: makeSeg({
        day_date: dayDate,
        start: args.start,
        end: endOfDay,
        continuesPrev: false,
        continuesNext: true,
        input,
      }),
    },
    {
      day_date: nextDay,
      seg: makeSeg({
        day_date: nextDay,
        start: startOfDay,
        end: args.end,
        continuesPrev: true,
        continuesNext: false,
        input,
      }),
    },
  ];
}
