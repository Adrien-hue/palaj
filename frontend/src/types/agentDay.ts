import { Tranche } from "./tranche";

export type AgentDay = {
  day_date: string; // "YYYY-MM-DD"
  day_type: "working" | "rest" | "absence" | string;
  description: string | null;
  is_off_shift: boolean;
  tranches: Tranche[];
};

export type AgentDayPutDTO = {
  day_type: string;
  description: string | null;
  tranche_id: number | null;
};