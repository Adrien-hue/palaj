export type Tranche = {
  id: number;
  nom: string;
  heure_debut: string; // "06:00:00"
  heure_fin: string;   // "14:00:00"
  poste_id: number;
};

export type CreateTrancheBody = {
  nom: string;
  heure_debut: string; // "HH:MM:SS"
  heure_fin: string;   // "HH:MM:SS"
  poste_id: number;
};

export type UpdateTrancheBody = Partial<{
  nom: string;
  heure_debut: string; // "HH:MM:SS"
  heure_fin: string;   // "HH:MM:SS"
}>;