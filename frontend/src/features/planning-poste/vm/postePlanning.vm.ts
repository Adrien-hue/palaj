import type { Agent, Poste, Tranche } from "@/types";

export type PosteShiftSegmentVm = {
  key: string;
  sourceTrancheId: number;

  nom: string;
  posteId: number;

  start: string; // "HH:MM:SS"
  end: string;   // "HH:MM:SS"

  continuesPrev: boolean;
  continuesNext: boolean;

  agent: Agent;

  agents?: Agent[];
};

export type PosteTrancheVm = {
  tranche: Tranche;
  agents: Agent[];
};

export type PosteDayVm = {
  day_date: string;
  day_type: string;
  description: string | null;
  is_off_shift: boolean;

  tranches: PosteTrancheVm[];

  segments: PosteShiftSegmentVm[];

  coverage: {
    total: number;
    covered: number;
  };
};

export type PostePlanningVm = {
  poste: Poste;
  start_date: string;
  end_date: string;
  days: PosteDayVm[];
};
