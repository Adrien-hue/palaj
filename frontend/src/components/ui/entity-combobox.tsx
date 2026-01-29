"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command";

export type EntityComboboxItem = {
  id: string | number;
  label: string;
  description?: string;
  keywords?: string;
};

export function EntityCombobox({
  items,
  value,
  onChange,
  placeholder = "Sélectionner…",
  searchPlaceholder = "Rechercher…",
  emptyText = "Aucun résultat.",
  disabled,
  buttonClassName,
  contentClassName,
}: {
  items: EntityComboboxItem[];
  value: string | number | null;
  onChange: (id: string | number) => void;

  placeholder?: string;
  searchPlaceholder?: string;
  emptyText?: string;
  disabled?: boolean;

  buttonClassName?: string;
  contentClassName?: string;
}) {
  const [open, setOpen] = React.useState(false);

  const selected = React.useMemo(
    () => items.find((x) => x.id === value) ?? null,
    [items, value]
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn("h-10 w-[320px] justify-between", buttonClassName)}
        >
          <span className="min-w-0 truncate">
            {selected ? selected.label : placeholder}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-60" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className={cn("w-[360px] p-0", contentClassName)} align="start">
        <Command>
          <CommandInput placeholder={searchPlaceholder} />
          <CommandEmpty>{emptyText}</CommandEmpty>

          <CommandGroup>
            {items.map((it) => {
              const isSelected = value === it.id;
              const v = `${it.id} ${it.label} ${it.keywords ?? ""}`.trim();

              return (
                <CommandItem
                  key={String(it.id)}
                  value={v}
                  onSelect={() => {
                    onChange(it.id);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn("mr-2 h-4 w-4", isSelected ? "opacity-100" : "opacity-0")}
                  />

                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{it.label}</div>
                    {it.description ? (
                      <div className="truncate text-xs text-muted-foreground">
                        {it.description}
                      </div>
                    ) : null}
                  </div>
                </CommandItem>
              );
            })}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
