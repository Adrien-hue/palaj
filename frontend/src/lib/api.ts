const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

if (!BASE_URL) {
  throw new Error("Missing NEXT_PUBLIC_API_URL in .env.local");
}

type FetchOptions = Omit<RequestInit, "body"> & { body?: unknown };

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    // Si ton backend utilise cookies/session plus tard:
    // credentials: "include",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText} - ${text}`);
  }

  // si endpoint vide (204)
  if (res.status === 204) return undefined as T;

  return (await res.json()) as T;
}
