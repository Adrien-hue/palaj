const BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!BASE_URL) throw new Error("Missing NEXT_PUBLIC_API_URL in .env.local");

type FetchOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  retry?: boolean;
};

function buildUrl(path: string) {
  return `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseJsonOrUndefined<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json"))
    return undefined as unknown as T;
  return (await res.json()) as T;
}

// --- CLIENT IMPLEMENTATION ---
async function apiFetchClient<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const url = buildUrl(path);
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

  if (res.status === 401 && options.retry !== false) {
    const refresh = await fetch(buildUrl("/auth/refresh"), {
      method: "POST",
      credentials: "include",
      headers: { Accept: "application/json" },
    });

    if (refresh.ok) {
      return apiFetchClient<T>(path, { ...options, retry: false });
    }

    // navigateur uniquement
    const next = window.location.pathname + window.location.search;
    window.location.href = `/login?next=${encodeURIComponent(next)}&reason=expired`;
    throw new Error("Session expirée");
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText} - ${text}`);
  }

  return parseJsonOrUndefined<T>(res);
}

// --- SERVER IMPLEMENTATION (cookies forward) ---
async function apiFetchServer<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const url = buildUrl(path);
  const hasBody = options.body !== undefined;

  // Import dynamique -> jamais bundlé côté client
  const { cookies } = await import("next/headers");

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const res = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
      ...(options.headers ?? {}),
    },
    body: hasBody ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText} - ${text}`);
  }

  return parseJsonOrUndefined<T>(res);
}

// --- UNIVERSAL EXPORT ---
export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  if (typeof window === "undefined") {
    return apiFetchServer<T>(path, options);
  }
  return apiFetchClient<T>(path, options);
}
