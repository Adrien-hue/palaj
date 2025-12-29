import type { Affectation } from "./affectation"; 
import type { EtatJourAgent } from "./etatJourAgent"; 
import type { Qualification } from "./qualification";
import type { Regime } from "./regimes";

export type Agent = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string;
  actif: boolean;
};

export type AgentDetails = Agent & {
  regime_id?: number | null;
  regime?: Regime | null;
  qualifications?: Qualification[];
  affectations?: Affectation[];
  etat_jours?: EtatJourAgent[];
};

export type CreateAgentBody = {
  nom: string;
  prenom: string;
  code_personnel?: string;
  regime_id?: number | null;
  actif?: boolean;
};

export type PatchAgentBody = {
  nom?: string | null;
  prenom?: string | null;
  code_personnel?: string | null;
  regime_id?: number | null;
  actif?: boolean | null;
};