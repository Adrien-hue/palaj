import { Tranche } from "./tranche";

export type PosteCoverageRequirement = {
  weekday: number;      // 0..6
  tranche_id: number;
  required_count: number;
};

type PosteCoverageBase = {
    poste_id: number;
    requirements: PosteCoverageRequirement[];
}

export type PosteCoverageDto = PosteCoverageBase & {
  tranches: Tranche[];
};

export type PosteCoveragePutDto = PosteCoverageBase

export type PosteCoverageDayDTO = {
  poste_id: number;
  day_date: string; // "YYYY-MM-DD"
  weekday: number;
  tranches: Array<{
    tranche_id: number;
    tranche_nom: string;
    heure_debut: string; // "HH:MM:SS"
    heure_fin: string;   // "HH:MM:SS"
    required_count: number;
    assigned_count: number;
  }>;
};