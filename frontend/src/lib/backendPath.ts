const API_PREFIX = "/backend/api/v1";

export function backendPath(path: string) {
  return `${API_PREFIX}${path.startsWith("/") ? path : `/${path}`}`;
}
