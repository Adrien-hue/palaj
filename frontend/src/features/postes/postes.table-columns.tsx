"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Eye, Pencil, Trash2 } from "lucide-react";

import type { Poste } from "@/types";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function getPosteTableColumns(opts: {
  onView: (p: Poste) => void;
  onEdit: (p: Poste) => void;
  onDelete: (p: Poste) => void;
}): ColumnDef<Poste, any>[] {
  return [
    {
      accessorKey: "nom",
      header: "Nom",
      cell: ({ row }) => {
        const p = row.original;
        return <span className="font-medium">{p.nom}</span>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => {
        const p = row.original;

        return (
          <div className="flex justify-end">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Ouvrir le menu</span>
                </Button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem onClick={() => opts.onView(p)}>
                  <Eye className="mr-2 h-4 w-4" />
                  Voir
                </DropdownMenuItem>

                <DropdownMenuItem onClick={() => opts.onEdit(p)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Éditer
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem
                  onClick={() => opts.onDelete(p)}
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
