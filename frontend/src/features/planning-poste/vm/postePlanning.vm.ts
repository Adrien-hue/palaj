import type { Agent, Poste, Tranche } from "@/types";

export type PosteShiftSegmentVm = {
  key: string;
  sourceTrancheId: number;

  nom: string;
  posteId: number;

  start: string; // "HH:MM:SS"
  end: string; // "HH:MM:SS"

  continuesPrev: boolean;
  continuesNext: boolean;

  agent: Agent;

  agents?: Agent[];

  color: string | null;
};

export type PosteTrancheVm = {
  tranche: Tranche;
  agents: Agent[];

  coverage?: {
    required: number;
    assigned: number;
    delta: number;
    isConfigured: boolean;
  };
};

export type PosteDayVm = {
  day_date: string;
  day_type: string;
  description: string | null;
  is_off_shift: boolean;

  tranches: PosteTrancheVm[];

  segments: PosteShiftSegmentVm[];

  coverage: {
    required: number;
    assigned: number;
    missing: number;
    isConfigured: boolean;
  };
};

export type PostePlanningVm = {
  poste: Poste;
  start_date: string;
  end_date: string;
  days: PosteDayVm[];
};
