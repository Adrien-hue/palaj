"use client";

import * as React from "react";

import type {
  JobStatus,
  PlanningGenerateRequest,
  PlanningGenerateResponse,
} from "./useTeamPlanningGenerate";

export type PlanningGenerateHistoryItem = {
  job_id: string;
  draft_id?: number;
  team_id: number;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
  last_seen_at: string;
  status_last_known: JobStatus;
};

type StorageShapeV1 = {
  version: 1;
  items: PlanningGenerateHistoryItem[];
};

type GenerateRequestContext = Pick<
  PlanningGenerateRequest,
  "team_id" | "start_date" | "end_date"
>;

const HISTORY_STORAGE_KEY = "planning_auto_generate_history_v1";
const LAST_JOB_STORAGE_KEY = "planning_auto_generate_last_job_id";
const HISTORY_LIMIT = 10;

function emptyStorage(): StorageShapeV1 {
  return { version: 1, items: [] };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isValidStatus(status: unknown): status is JobStatus {
  return status === "queued" || status === "running" || status === "success" || status === "failed";
}

function normalizeItem(value: unknown): PlanningGenerateHistoryItem | null {
  if (!isObject(value)) return null;

  const {
    job_id,
    draft_id,
    team_id,
    start_date,
    end_date,
    created_at,
    updated_at,
    last_seen_at,
    status_last_known,
  } = value;

  if (
    typeof job_id !== "string" ||
    typeof team_id !== "number" ||
    typeof start_date !== "string" ||
    typeof end_date !== "string" ||
    typeof created_at !== "string" ||
    !isValidStatus(status_last_known)
  ) {
    return null;
  }

  return {
    job_id,
    draft_id: typeof draft_id === "number" ? draft_id : undefined,
    team_id,
    start_date,
    end_date,
    created_at,
    updated_at: typeof updated_at === "string" ? updated_at : created_at,
    last_seen_at: typeof last_seen_at === "string" ? last_seen_at : created_at,
    status_last_known,
  };
}

function sortAndTrim(items: PlanningGenerateHistoryItem[]) {
  return [...items]
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, HISTORY_LIMIT);
}

function migrateToV1(parsed: unknown): StorageShapeV1 {
  if (Array.isArray(parsed)) {
    return {
      version: 1,
      items: sortAndTrim(
        parsed
          .map(normalizeItem)
          .filter((i): i is PlanningGenerateHistoryItem => i !== null),
      ),
    };
  }

  if (isObject(parsed) && Array.isArray(parsed.items)) {
    return {
      version: 1,
      items: sortAndTrim(
        parsed.items
          .map(normalizeItem)
          .filter((i): i is PlanningGenerateHistoryItem => i !== null),
      ),
    };
  }

  return emptyStorage();
}

function safeRead(): StorageShapeV1 {
  if (typeof window === "undefined") return emptyStorage();

  try {
    const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) return emptyStorage();

    const parsed = JSON.parse(raw) as unknown;

    // Migration best-effort: anciens formats sans version (array direct ou {items})
    if (!isObject(parsed) || parsed.version !== 1) {
      return migrateToV1(parsed);
    }

    if (!Array.isArray(parsed.items)) {
      return emptyStorage();
    }

    const normalized = parsed.items
      .map(normalizeItem)
      .filter((i): i is PlanningGenerateHistoryItem => i !== null);

    return { version: 1, items: sortAndTrim(normalized) };
  } catch {
    return emptyStorage();
  }
}

function writeStorage(storage: StorageShapeV1) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(storage));
}

function upsertByJobId(
  items: PlanningGenerateHistoryItem[],
  incoming: PlanningGenerateHistoryItem,
): PlanningGenerateHistoryItem[] {
  const idx = items.findIndex((item) => item.job_id === incoming.job_id);
  if (idx === -1) return sortAndTrim([incoming, ...items]);

  const curr = items[idx];
  const next = [...items];
  next[idx] = {
    ...curr,
    ...incoming,
    draft_id: incoming.draft_id ?? curr.draft_id,
    created_at: curr.created_at,
  };
  return sortAndTrim(next);
}

function readLastJobId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(LAST_JOB_STORAGE_KEY);
}

export function usePlanningGenerateHistory() {
  const [storage, setStorage] = React.useState<StorageShapeV1>(() => safeRead());
  const [lastJobId, setLastJobIdState] = React.useState<string | null>(() => readLastJobId());
  const itemsRef = React.useRef<PlanningGenerateHistoryItem[]>(storage.items);

  React.useEffect(() => {
    itemsRef.current = storage.items;
  }, [storage.items]);

  const setLastJobId = React.useCallback((jobId: string | null) => {
    setLastJobIdState((prev) => (prev === jobId ? prev : jobId));

    if (typeof window === "undefined") return;

    if (!jobId) {
      window.localStorage.removeItem(LAST_JOB_STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(LAST_JOB_STORAGE_KEY, jobId);
  }, []);

  const upsertHistoryItem = React.useCallback((item: PlanningGenerateHistoryItem) => {
    setStorage((prev) => {
      const nextItems = upsertByJobId(prev.items, item);
      if (nextItems === prev.items) return prev;

      const unchanged =
        nextItems.length === prev.items.length &&
        nextItems.every((it, idx) => it === prev.items[idx]);
      if (unchanged) return prev;

      const next: StorageShapeV1 = {
        version: 1,
        items: nextItems,
      };
      itemsRef.current = next.items;
      writeStorage(next);
      return next;
    });
  }, []);

  const upsertFromGenerateResponse = React.useCallback(
    (response: PlanningGenerateResponse, context: GenerateRequestContext) => {
      const now = new Date().toISOString();
      upsertHistoryItem({
        job_id: response.job_id,
        draft_id: response.draft_id,
        team_id: context.team_id,
        start_date: context.start_date,
        end_date: context.end_date,
        created_at: now,
        updated_at: now,
        last_seen_at: now,
        status_last_known: response.status,
      });
    },
    [upsertHistoryItem],
  );

  const updateStatus = React.useCallback(
    (jobId: string, status: JobStatus, draftId?: number) => {
      setStorage((prev) => {
        const current = prev.items.find((item) => item.job_id === jobId);
        if (!current) return prev;

        if (
          current.status_last_known === status &&
          (draftId == null || current.draft_id === draftId)
        ) {
          return prev;
        }

        const now = new Date().toISOString();
        const next: StorageShapeV1 = {
          version: 1,
          items: upsertByJobId(prev.items, {
            ...current,
            status_last_known: status,
            draft_id: draftId ?? current.draft_id,
            updated_at: now,
            last_seen_at: now,
          }),
        };

        itemsRef.current = next.items;
        writeStorage(next);
        return next;
      });
    },
    [],
  );

  const select = React.useCallback(
    (jobId: string) => itemsRef.current.find((item) => item.job_id === jobId) ?? null,
    [],
  );

  const selectDraft = React.useCallback(
    (draftId: number) => itemsRef.current.find((item) => item.draft_id === draftId) ?? null,
    [],
  );

  const clear = React.useCallback(() => {
    setStorage((prev) => {
      const next = emptyStorage();
      if (prev.items.length === 0) {
        itemsRef.current = next.items;
        return prev;
      }

      itemsRef.current = next.items;
      writeStorage(next);
      return next;
    });
    setLastJobId(null);
  }, [setLastJobId]);

  return {
    history: storage.items,
    lastJobId,
    setLastJobId,
    upsertHistoryItem,
    upsertFromGenerateResponse,
    updateStatus,
    select,
    selectDraft,
    clear,
  };
}
