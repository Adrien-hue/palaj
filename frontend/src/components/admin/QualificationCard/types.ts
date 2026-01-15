// frontend/src/components/admin/QualificationCard/types.ts
import type { Qualification } from "@/types";

export type QualificationMode = "agent" | "poste";

export type QualificationOption = {
  id: number;
  label: string; // Poste.nom or "NOM Prénom"
};

export type RowVM = {
  relatedId: number;
  label: string;
  date: string; // YYYY-MM-DD or ""
};

export type QualificationCardProps = {
  title: string;
  mode: QualificationMode;
  qualifications: Qualification[];

  /**
   * Provides selectable options (postes or agents).
   * Parent should memoize it (useCallback) to avoid re-fetching on each render.
   */
  loadOptions: () => Promise<QualificationOption[]>;

  /** Disables the whole card during parent mutations */
  disabled?: boolean;

  // Callbacks (parent is responsible for calling API)
  onAdd: (payload: { related_id: number; date_qualification: string }) => Promise<void> | void;
  onUpdateDate: (payload: { related_id: number; date_qualification: string }) => Promise<void> | void;
  onDelete: (payload: { related_id: number }) => Promise<void> | void;

  /** Confirmation is injected so the card is UI-agnostic (ConfirmDialog or anything else). */
  confirmDelete: (label: string) => Promise<boolean>;
};
