export type Qualification = {
  agent_id: number;
  poste_id: number;
  date_qualification: string | null;
};

export type CreateQualificationBody = {
  agent_id: number;
  poste_id: number;
  date_qualification: string | null;
};

export type UpdateQualificationBody = {
  date_qualification: string;
};

export type SearchQualificationsParams = {
  agent_id?: number | null;
  poste_id?: number | null;
};