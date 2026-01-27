export type TeamBase = {
    name: string;
    description?: string | null;
}

export type Team = TeamBase & {
    id: number;
    created_at: string;
}

export type CreateTeamBody = TeamBase;

export type PatchTeamBody = {
  name?: string;
  description?: string | null;
};
