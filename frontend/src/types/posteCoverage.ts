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