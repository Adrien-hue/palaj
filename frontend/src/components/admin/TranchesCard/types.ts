// frontend/src/components/admin/TranchesCard/types.ts
import type { Tranche } from "@/types";

export type TrancheDraft = {
  nom: string;
  heure_debut: string; // "HH:MM" for input
  heure_fin: string; // "HH:MM" for input
  color?: string | null;
};

export type TranchesCardProps = {
  title: string;
  tranches: Tranche[];

  disabled?: boolean;

  onAdd: (payload: {
    nom: string;
    heure_debut: string;
    heure_fin: string;
  }) => Promise<void> | void;
  onUpdate: (
    trancheId: number,
    payload: { nom: string; heure_debut: string; heure_fin: string; color?: string | null }
  ) => Promise<void> | void;
  onDelete: (trancheId: number) => Promise<void> | void;

  confirmDelete: (label: string) => Promise<boolean>;
};

export type TranchesTimelineProps = {
  tranches: Tranche[];
  markerEveryHours?: number; // default: 3
  onSelectTranche?: (trancheId: number) => void;
};

export type TimelineTooltipState = null | {
  text: string;
  x: number;
  y: number;
};

export type TrancheSegment = {
  startMin: number; // 0..1440
  endMin: number; // 0..1440 (end > start)
};
