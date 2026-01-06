export type Tranche = {
  id: number;
  nom: string;
  heure_debut: string; // "06:00:00"
  heure_fin: string;   // "14:00:00"
  poste_id: number;
};

export type TrancheSegmentUi = {
  key: string;               // unique
  source_tranche_id: number; // id d’origine
  nom: string;
  poste_id: number;
  start: string; // "HH:MM:SS"
  end: string;   // "HH:MM:SS"
  continues_prev: boolean;
  continues_next: boolean;
};
