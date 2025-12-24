"use client";

import type { ReactNode, RefObject } from "react";
import type { ColumnDef } from "./DataTable";
import { DataTable } from "./DataTable";
import { Pagination } from "./Pagination";
import { useListing } from "./useListing";
import { ListResponse } from "@/types";

export function ListPage<T>({
  title,
  description,
  fetcher,
  columns,
  getRowId,
  headerRight,
  emptyTitle = "Aucun résultat",
  emptyDescription = "Aucune donnée à afficher pour le moment.",
  listingRef,
  pageSizeOptions = true,
}: {
  title: string;
  description?: string;
  fetcher: (args: { page: number; pageSize: number }) => Promise<ListResponse<T>>;
  columns: ColumnDef<T>[];
  getRowId: (row: T) => string | number;
  headerRight?: ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
  listingRef?: RefObject<{ refresh: () => void }>;
  pageSizeOptions?: boolean;
}) {
  const listing = useListing<T>({
    fetcher,
    initialPage: 1,
    initialPageSize: 10,
  });

  if (listingRef) {
    (listingRef as React.RefObject<{ refresh: () => void }>).current = {
      refresh: listing.refresh,
    };
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold">{title}</h1>
          {description && (
            <p className="mt-1 text-sm text-zinc-600">{description}</p>
          )}
        </div>
        {headerRight}
      </div>

      {/* States */}
      {listing.loading && (
        <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
          Chargement…
        </div>
      )}

      {!listing.loading && listing.error && (
        <div className="rounded-2xl bg-white p-4 ring-1 ring-red-200">
          <div className="text-sm font-medium text-red-700">Erreur</div>
          <div className="mt-1 text-sm text-red-700">{listing.error}</div>
          <button
            className="mt-3 rounded-xl bg-zinc-900 px-3 py-2 text-sm text-white hover:bg-zinc-800"
            onClick={listing.refresh}
          >
            Réessayer
          </button>
        </div>
      )}

      {!listing.loading &&
        !listing.error &&
        listing.data &&
        listing.data.items.length === 0 && (
          <div className="rounded-2xl bg-white p-6 ring-1 ring-zinc-200">
            <div className="text-sm font-medium">{emptyTitle}</div>
            <div className="mt-1 text-sm text-zinc-600">{emptyDescription}</div>
          </div>
        )}

      {!listing.loading &&
        !listing.error &&
        listing.data &&
        listing.data.items.length > 0 && (
          <div className="flex min-h-0 flex-1 flex-col">
            <div className="min-h-0 flex-1">
              <DataTable<T>
                columns={columns}
                rows={listing.data.items}
                getRowId={getRowId}
                // ajuste la hauteur de table si besoin
                maxHeightClassName="max-h-[calc(100dvh-320px)]"
              />
            </div>

            <div className="mt-3 shrink-0">
              <Pagination
                page={listing.page}
                totalPages={listing.totalPages}
                total={listing.total}
                pageSize={listing.pageSize}
                onPrev={() => listing.setPage(Math.max(1, listing.page - 1))}
                onNext={() => listing.setPage(listing.page + 1)}
                onPageSizeChange={
                  pageSizeOptions ? listing.setPageSize : undefined
                }
              />
            </div>
          </div>
        )}
    </div>
  );
}
