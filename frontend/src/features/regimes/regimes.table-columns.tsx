"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Eye, Pencil, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import type { Regime } from "@/types";

export function getRegimeColumns(opts: {
  onView: (r: Regime) => void;
  onEdit: (r: Regime) => void;
  onDelete: (r: Regime) => void;
}): ColumnDef<Regime, unknown>[] {
  return [
    {
      accessorKey: "nom",
      header: "Nom",
      cell: ({ row }) => <div className="font-medium">{row.original.nom}</div>,
    },
    {
      accessorKey: "desc",
      header: "Description",
      cell: ({ row }) => (
        <div className="max-w-[520px] truncate text-muted-foreground">
          {row.original.desc || "—"}
        </div>
      ),
    },
    {
      id: "actions",
      enableHiding: false,
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => {
        const r = row.original;
        return (
          <div className="flex justify-end">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Actions">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => opts.onView(r)}>
                  <Eye className="mr-2 h-4 w-4" />
                  Détails
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => opts.onEdit(r)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Modifier
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem
                  onClick={() => opts.onDelete(r)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Supprimer
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        );
      },
    },
  ];
}
