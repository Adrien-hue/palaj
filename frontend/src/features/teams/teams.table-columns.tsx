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

import type { Team } from "@/types";

function formatDateTime(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";

  // format simple, cohérent et lisible
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

export function getTeamColumns(opts: {
  onView: (t: Team) => void;
  onEdit: (t: Team) => void;
  onDelete: (t: Team) => void;
}): ColumnDef<Team, unknown>[] {
  return [
    {
      accessorKey: "name",
      header: "Nom",
      cell: ({ row }) => <div className="font-medium">{row.original.name}</div>,
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => (
        <div className="max-w-[520px] truncate text-muted-foreground">
          {row.original.description || "—"}
        </div>
      ),
    },
    {
      accessorKey: "created_at",
      header: "Créée le",
      cell: ({ row }) => (
        <div className="whitespace-nowrap text-muted-foreground">
          {formatDateTime(row.original.created_at)}
        </div>
      ),
    },
    {
      id: "actions",
      enableHiding: false,
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => {
        const t = row.original;

        return (
          <div className="flex justify-end">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Actions">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => opts.onView(t)}>
                  <Eye className="mr-2 h-4 w-4" />
                  Détails
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => opts.onEdit(t)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Modifier
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem
                  onClick={() => opts.onDelete(t)}
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
