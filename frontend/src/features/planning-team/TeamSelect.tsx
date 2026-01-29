"use client";

import * as React from "react";
import type { Team } from "@/types";

import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function TeamSelect(props: {
  teams: Team[];
  value: number | null;
  onChange: (teamId: number) => void;
  disabled?: boolean;
}) {
  const { teams, value, onChange, disabled } = props;
  const [open, setOpen] = React.useState(false);

  const selected = teams.find((t) => t.id === value) ?? null;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[260px] justify-between"
          disabled={disabled}
        >
          <span className="truncate">
            {selected ? selected.name : "Choisir une équipe…"}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 opacity-60" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-[320px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Rechercher une équipe…" />
          <CommandEmpty>Aucune équipe trouvée.</CommandEmpty>
          <CommandGroup>
            {teams.map((t) => (
              <CommandItem
                key={t.id}
                value={`${t.id}-${t.name}`}
                onSelect={() => {
                  onChange(t.id);
                  setOpen(false);
                }}
              >
                <Check className={cn("mr-2 h-4 w-4", value === t.id ? "opacity-100" : "opacity-0")} />
                <div className="flex flex-col">
                  <span className="font-medium">{t.name}</span>
                  {t.description ? (
                    <span className="text-xs text-muted-foreground truncate max-w-[260px]">
                      {t.description}
                    </span>
                  ) : null}
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
