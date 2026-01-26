"use client";

import type { ColumnDef } from "@/components/admin/listing/DataTable";
import type { Agent } from "@/types";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { MoreHorizontal, Eye, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function getAgentColumns(opts: {
  onView: (a: Agent) => void;
  onEdit: (a: Agent) => void;
  onDelete: (a: Agent) => void;
  onToggleActive: (a: Agent) => void;
  togglingIds?: Set<number>;
}): ColumnDef<Agent>[] {
  return [
    {
      key: "nom",
      header: "Nom",
      cell: (a) => <span className="font-medium">{a.nom}</span>,
    },
    {
      key: "prenom",
      header: "Prénom",
      cell: (a) => a.prenom,
    },
    {
      key: "code",
      header: "Code",
      cell: (a) => (
        <span className="text-muted-foreground">
          {a.code_personnel}
        </span>
      ),
    },
    {
      key: "actif",
      header: "Actif",
      cell: (a) => {
        const toggling = opts.togglingIds?.has(a.id) ?? false;
        const label = a.actif
          ? "Désactiver l’agent"
          : "Activer l’agent";

        return (
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  "inline-flex items-center",
                  toggling && "opacity-60 cursor-not-allowed"
                )}
              >
                <Switch
                  checked={a.actif}
                  disabled={toggling}
                  onCheckedChange={() => opts.onToggleActive(a)}
                  aria-label={label}
                />
              </div>
            </TooltipTrigger>
            <TooltipContent>{label}</TooltipContent>
          </Tooltip>
        );
      },
    },
    {
      key: "actions",
      header: "",
      headerClassName: "w-[72px]",
      className: "text-right",
      cell: (a) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
            >
              <MoreHorizontal className="h-4 w-4" />
              <span className="sr-only">Ouvrir le menu</span>
            </Button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>

            <DropdownMenuItem onClick={() => opts.onView(a)}>
              <Eye className="mr-2 h-4 w-4" />
              Voir
            </DropdownMenuItem>

            <DropdownMenuItem onClick={() => opts.onEdit(a)}>
              <Pencil className="mr-2 h-4 w-4" />
              Éditer
            </DropdownMenuItem>

            <DropdownMenuSeparator />

            <DropdownMenuItem
              onClick={() => opts.onDelete(a)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Supprimer
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];
}
