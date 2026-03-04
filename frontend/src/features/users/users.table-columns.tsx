"use client";

import type { ColumnDef } from "@tanstack/react-table";
import type { User } from "@/types";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { MoreHorizontal, Eye, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function getUsersTableColumns(opts: {
  onView: (u: User) => void;
  onEdit: (u: User) => void;
  onDelete: (u: User) => void;
  onToggleActive: (u: User) => void;
  togglingIds?: Set<number>;
  currentUserId?: number | null;
}): ColumnDef<User>[] {
  return [
    {
      accessorKey: "username",
      header: "Nom d’utilisateur",
      cell: ({ row }) => <span className="font-medium">{row.original.username}</span>,
    },
    {
      accessorKey: "role",
      header: "Rôle",
      cell: ({ row }) => {
        const role = row.original.role;

        return (
          <Badge variant={role === "admin" ? "destructive" : "secondary"} className="capitalize">
            {role}
          </Badge>
        );
      },
    },
    {
      id: "is_active",
      header: "Statut",
      cell: ({ row }) => {
        const u = row.original;
        const toggling = opts.togglingIds?.has(u.id) ?? false;
        const isSelf = opts.currentUserId === u.id;
        const label = u.is_active ? "Désactiver l’utilisateur" : "Activer l’utilisateur";

        return (
          <div className="inline-flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className={cn(
                    "inline-flex items-center",
                    (toggling || isSelf) && "opacity-60 cursor-not-allowed"
                  )}
                >
                  <Switch
                    checked={u.is_active}
                    disabled={toggling || isSelf}
                    onCheckedChange={() => opts.onToggleActive(u)}
                    aria-label={label}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                {isSelf ? "Impossible de modifier son propre statut" : label}
              </TooltipContent>
            </Tooltip>

            <Badge
              variant="secondary"
              className={cn(
                u.is_active
                  ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {u.is_active ? "Actif" : "Inactif"}
            </Badge>
          </div>
        );
      },
      enableSorting: false,
    },
    {
      id: "actions",
      header: "",
      size: 80,
      maxSize: 80,
      cell: ({ row }) => {
        const u = row.original;
        const isSelf = opts.currentUserId === u.id;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Ouvrir le menu</span>
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>

              <DropdownMenuItem onClick={() => opts.onView(u)}>
                <Eye className="mr-2 h-4 w-4" />
                Voir
              </DropdownMenuItem>

              <DropdownMenuItem onClick={() => opts.onEdit(u)}>
                <Pencil className="mr-2 h-4 w-4" />
                Éditer
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              <DropdownMenuItem
                onClick={() => !isSelf && opts.onDelete(u)}
                disabled={isSelf}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Supprimer
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
      enableHiding: false,
      enableSorting: false,
    },
  ];
}
