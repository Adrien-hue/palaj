export type MonthPeriod = {
  kind: "month";
  month: Date;
};

export type RangePeriod = {
  kind: "range";
  start: Date;
  end: Date;
};

export type PlanningPeriod = MonthPeriod | RangePeriod;
