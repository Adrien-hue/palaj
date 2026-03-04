import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { ListResponse } from "@/types/api";
import type { CreateUserBody, UpdateUserBody, User } from "@/types";

type ListUsersParams = {
  include_inactive?: boolean;
};

export async function listUsers(params: ListUsersParams = {}) {
  const search = new URLSearchParams();
  if (params.include_inactive != null) {
    search.set("include_inactive", String(params.include_inactive));
  }

  const qs = search.toString();
  const res = await apiFetch<User[] | ListResponse<User>>(
    backendPath(`/users${qs ? `?${qs}` : ""}`)
  );

  if (Array.isArray(res)) return res;
  return res.items;
}

export async function getUser(id: number) {
  return apiFetch<User>(backendPath(`/users/${id}`));
}

export async function createUser(payload: CreateUserBody) {
  return apiFetch<User>(backendPath("/users"), { method: "POST", body: payload });
}

export async function updateUser(id: number, payload: UpdateUserBody) {
  return apiFetch<User>(backendPath(`/users/${id}`), { method: "PATCH", body: payload });
}

export async function deleteUser(id: number) {
  return apiFetch<void>(backendPath(`/users/${id}`), { method: "DELETE" });
}
