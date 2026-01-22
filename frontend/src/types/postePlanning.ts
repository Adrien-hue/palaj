import { Agent } from "./agent";
import { Poste } from "./postes";
import { Tranche } from "./tranche";


export type PostePlanning = {
  poste: Poste;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  days: Array<{
    day_date: string; // YYYY-MM-DD
    day_type: string;
    description: string;
    is_off_shift: boolean;
    tranches: Array<{
      tranche: Tranche;
      agents: Array<Agent>;
    }>;
  }>;
};
