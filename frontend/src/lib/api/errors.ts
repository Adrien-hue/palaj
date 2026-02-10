// frontend/src/lib/api/errors.ts
export type ApiErrorDetail =
  | string
  | number
  | boolean
  | null
  | Record<string, unknown>
  | unknown[];

export class ApiError extends Error {
  readonly status: number;
  readonly statusText: string;

  /** Raw response body (best-effort), useful for logs */
  readonly bodyText?: string;

  /** Parsed JSON body (if any) */
  readonly bodyJson?: unknown;

  /** Common API field (FastAPI uses {"detail": ...}) */
  readonly detail?: ApiErrorDetail;

  constructor(args: {
    message: string;
    status: number;
    statusText: string;
    bodyText?: string;
    bodyJson?: unknown;
    detail?: ApiErrorDetail;
  }) {
    super(args.message);
    this.name = "ApiError";
    this.status = args.status;
    this.statusText = args.statusText;
    this.bodyText = args.bodyText;
    this.bodyJson = args.bodyJson;
    this.detail = args.detail;
  }
}

type ApiErrorArgs = Omit<
  ConstructorParameters<typeof ApiError>[0],
  "message" | "status" | "statusText"
>;

export class UnauthorizedError extends ApiError {
  constructor(args: ApiErrorArgs = {}) {
    super({ message: "Not authenticated", status: 401, statusText: "Unauthorized", ...args });
    this.name = "UnauthorizedError";
  }
}

/**
 * Used when:
 * - we received a 401
 * - we attempted refresh
 * - refresh failed
 */
export class AuthExpiredError extends ApiError {
  constructor(args: ApiErrorArgs = {}) {
    super({ message: "Session expired", status: 401, statusText: "Unauthorized", ...args });
    this.name = "AuthExpiredError";
  }
}

export class ForbiddenError extends ApiError {
  constructor(args: ApiErrorArgs = {}) {
    super({ message: "Forbidden", status: 403, statusText: "Forbidden", ...args });
    this.name = "ForbiddenError";
  }
}
