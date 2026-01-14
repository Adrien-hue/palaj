import type { Qualification } from "./qualification";
import type { Tranche } from "./tranche";

export type Poste = {
  id: number;
  nom: string;
};

export type PosteDetail = Poste & {
  tranches: Tranche[];
  qualifications: Qualification[];
};

export type CreatePosteBody = {
  nom: string;
};

export type PatchPosteBody = {
  nom?: string;
};