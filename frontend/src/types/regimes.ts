import type { Agent } from "./agent";

export type RegimeBase = {
  nom: string;
  desc?: string | null;

  min_rp_annuels?: number | null;
  min_rp_dimanches?: number | null;
  min_rpsd?: number | null;
  min_rp_2plus?: number | null;
  min_rp_semestre?: number | null;

  avg_service_minutes?: number | null;
  avg_tolerance_minutes?: number | null;
};

export type Regime = RegimeBase & {
  id: number;
};

export type RegimeDetail = Regime & {
  agents: Agent[];
};

export type CreateRegimeBody = RegimeBase;

export type UpdateRegimeBody = Partial<RegimeBase>;
