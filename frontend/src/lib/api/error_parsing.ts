export async function readBody(
  res: Response,
): Promise<{ bodyText?: string; bodyJson?: unknown; detail?: unknown }> {
  const contentType = res.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      const bodyJson = await res.json();
      const detail = (bodyJson as any)?.detail;
      return { bodyJson, detail };
    } catch {
      // fallthrough to text
    }
  }

  try {
    const bodyText = await res.text();
    return { bodyText };
  } catch {
    return {};
  }
}

export function formatMessage(args: {
  status: number;
  statusText: string;
  detail?: unknown;
  bodyText?: string;
}): string {
  const { status, statusText, detail, bodyText } = args;

  if (typeof detail === "string" && detail.trim()) return detail;
  if (bodyText && bodyText.trim())
    return `API ${status} ${statusText} - ${bodyText}`;
  return `API ${status} ${statusText}`;
}
