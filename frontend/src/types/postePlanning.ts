import { Agent } from "./agent";
import { Poste } from "./postes";
import { Tranche } from "./tranche";

export type PostePlanningDayPutBody = {
  tranches: Array<{
    tranche_id: number;
    agent_ids: number[];
  }>;
  cleanup_empty_agent_days: boolean;
};

export type PostePlanningDay = {
  day_date: string; // YYYY-MM-DD
  day_type: string;
  description?: string | null;
  is_off_shift: boolean;
  tranches: Array<{
    tranche: Tranche;
    agents: Array<Agent>;
  }>;
};

export type PostePlanning = {
  poste: Poste;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  days: Array<PostePlanningDay>;
};
