export type ListMeta = {
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type ListParams = {
  page?: number;
  page_size?: number;
};

export type ListResponse<T> = {
  items: T[];
  meta: ListMeta;
};
