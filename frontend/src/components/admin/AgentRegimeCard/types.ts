import type { Regime } from "@/types";

export type RegimeOption = {
  id: number;
  label: string; // regime.nom
  hint?: string | null; // regime.desc (optional)
};

export type AgentRegimeCardProps = {
  title?: string;
  // current value
  regime: Pick<Regime, "id" | "nom" | "desc"> | null;

  // load select options (parent decides how)
  loadOptions: () => Promise<RegimeOption[]>;

  disabled?: boolean;

  // PATCH /agents/{id} with regime_id
  onChangeRegime: (regimeId: number) => Promise<void> | void;
  onClearRegime: () => Promise<void> | void;

  // confirm clear
  confirmClear: (label: string) => Promise<boolean>;
};
