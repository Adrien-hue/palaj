"use client";

import * as React from "react";
import type { ColumnDef } from "@tanstack/react-table";
import {
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Props<TData> = {
  data: TData[];
  columns: ColumnDef<TData, any>[];
  searchPlaceholder?: string;
  initialPageSize?: number;
  maxHeightClassName?: string;
  enableColumnVisibility?: boolean;
};

export function ClientDataTable<TData>({
  data,
  columns,
  searchPlaceholder = "Rechercher…",
  initialPageSize = 20,
  maxHeightClassName = "max-h-[60dvh]",
  enableColumnVisibility = true,
}: Props<TData>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [globalFilter, setGlobalFilter] = React.useState("");

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, columnVisibility, globalFilter },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onGlobalFilterChange: setGlobalFilter,

    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),

    globalFilterFn: "includesString",
    initialState: {
      pagination: { pageIndex: 0, pageSize: initialPageSize },
    },
  });

  const hideableColumns = table.getAllColumns().filter((c) => c.getCanHide());

  const canShowColumnVisibility =
    enableColumnVisibility && hideableColumns.length > 0;

  const filteredCount = table.getFilteredRowModel().rows.length;
  const totalCount = table.getPreFilteredRowModel().rows.length;

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Input
            value={globalFilter ?? ""}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full sm:w-[320px]"
          />

          {canShowColumnVisibility ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">Colonnes</Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {hideableColumns.map((column) => (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={column.getIsVisible()}
                    onCheckedChange={(v) => column.toggleVisibility(!!v)}
                  >
                    {String(column.columnDef.header ?? column.id)}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          ) : null}
        </div>

        <div className="text-sm text-muted-foreground">
          {filteredCount} / {totalCount} résultat(s)
        </div>
      </div>

      {/* Table */}
      <div className={["overflow-auto rounded-xl border bg-background", maxHeightClassName].join(" ")}>
        <Table>
          <TableHeader className="sticky top-0 z-20 bg-muted/50 backdrop-blur supports-[backdrop-filter]:bg-muted/40">
            {table.getHeaderGroups().map((hg) => (
              <TableRow key={hg.id}>
                {hg.headers.map((header) => (
                  <TableHead key={header.id} className="whitespace-nowrap">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>

          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className="hover:bg-muted/50">
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="align-middle">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={table.getAllLeafColumns().length}
                  className="h-24 text-center text-muted-foreground"
                >
                  Aucun résultat.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm text-muted-foreground">
          Page {table.getState().pagination.pageIndex + 1} /{" "}
          {table.getPageCount()}
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            {table.getCanPreviousPage() ? (
              <Button variant="outline" onClick={() => table.previousPage()}>
                Précédent
              </Button>
            ) : null}

            {table.getCanNextPage() ? (
              <Button variant="outline" onClick={() => table.nextPage()}>
                Suivant
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
