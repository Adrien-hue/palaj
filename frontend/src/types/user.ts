export type UserRole = "admin" | "manager";

export type User = {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
};

export type CreateUserBody = {
  username: string;
  password: string;
  role: UserRole;
  is_active: boolean;
};

export type UpdateUserBody = {
  username?: string;
  password?: string;
  role?: UserRole;
  is_active?: boolean;
};
