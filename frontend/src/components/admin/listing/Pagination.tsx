"use client";

export function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  onPrev,
  onNext,
  onPageSizeChange,
}: {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPrev: () => void;
  onNext: () => void;
  onPageSizeChange?: (s: number) => void;
}) {
  return (
    <div className="flex flex-col gap-2 rounded-2xl bg-white p-3 ring-1 ring-zinc-200 sm:flex-row sm:items-center sm:justify-between">
      <div className="text-sm text-zinc-600">
        Page <span className="font-medium text-zinc-900">{page}</span> /{" "}
        <span className="font-medium text-zinc-900">{totalPages}</span> —{" "}
        <span className="font-medium text-zinc-900">{total}</span> total
      </div>

      <div className="flex items-center gap-2 justify-between sm:justify-end">
        {onPageSizeChange && (
          <select
            className="rounded-xl px-2 py-2 text-sm ring-1 ring-zinc-200 bg-white"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            aria-label="Page size"
          >
            {[10, 20, 50, 100].map((s) => (
              <option key={s} value={s}>
                {s} par page
              </option>
            ))}
          </select>
        )}

        <div className="flex gap-2">
          <button
            className="rounded-xl px-3 py-2 text-sm ring-1 ring-zinc-200 hover:bg-zinc-50 disabled:opacity-50"
            disabled={page <= 1}
            onClick={onPrev}
          >
            Précédent
          </button>
          <button
            className="rounded-xl px-3 py-2 text-sm ring-1 ring-zinc-200 hover:bg-zinc-50 disabled:opacity-50"
            disabled={page >= totalPages}
            onClick={onNext}
          >
            Suivant
          </button>
        </div>
      </div>
    </div>
  );
}