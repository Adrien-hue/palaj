const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

if (!BASE_URL) throw new Error("Missing NEXT_PUBLIC_API_URL in .env.local");

type FetchOptions = Omit<RequestInit, "body"> & { body?: unknown; retry?: boolean };

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const hasBody = options.body !== undefined;

  const res = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...(options.headers ?? {}),
    },
    body: hasBody ? JSON.stringify(options.body) : undefined,
    credentials: "include",
  });

  // 401 -> refresh -> retry once
  if (res.status === 401 && options.retry !== false) {
    const refresh = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { Accept: "application/json" },
    });

    if (refresh.ok) {
      return apiFetch<T>(path, { ...options, retry: false });
    }

    if (typeof window !== "undefined") {
      const next = window.location.pathname + window.location.search;
      window.location.href = `/login?next=${encodeURIComponent(next)}&reason=expired`;
    }

    throw new Error("Session expirée");
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText} - ${text}`);
  }

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return (undefined as unknown) as T;
  }

  return (await res.json()) as T;
}
