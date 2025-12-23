export type Agent = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
};