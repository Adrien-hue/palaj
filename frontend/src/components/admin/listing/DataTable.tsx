// components/admin/listing/DataTable.tsx
import type { ReactNode } from "react";

export type ColumnDef<T> = {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
};

export function DataTable<T>({
  columns,
  rows,
  getRowId,
  maxHeightClassName = "max-h-[60dvh]",
}: {
  columns: ColumnDef<T>[];
  rows: T[];
  getRowId: (row: T) => string | number;
  maxHeightClassName?: string; // pour ajuster facilement
}) {
  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-zinc-200">
      <div className={["overflow-auto", maxHeightClassName].join(" ")}>
        <table className="w-full text-sm border-separate border-spacing-0">
          <thead>
            <tr>
              {columns.map((c) => (
                <th
                  key={c.key}
                  className={[
                    "px-4 py-3 text-left font-medium text-zinc-600",
                    "sticky top-0 z-20 bg-zinc-50",
                    "border-b border-zinc-200",
                    c.headerClassName ?? "",
                  ].join(" ")}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="[&>tr:last-child]:border-b-0">
            {rows.map((row) => (
              <tr
                key={getRowId(row)}
                className="border-b border-zinc-100 hover:bg-zinc-50"
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={[
                      "px-4 py-3 align-middle",
                      c.className ?? "",
                    ].join(" ")}
                  >
                    {c.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
