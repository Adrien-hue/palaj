export type Agent = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string;
  regime_id?: number;
  actif: boolean;
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