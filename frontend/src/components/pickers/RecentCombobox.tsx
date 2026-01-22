"use client";

import * as React from "react";
import { Check, ChevronsUpDown, Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";

function safeLoad<T>(key: string, max: number): T[] {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as T[];
    if (!Array.isArray(parsed)) return [];
    return parsed.slice(0, max);
  } catch {
    return [];
  }
}

function safeSave<T>(
  key: string,
  max: number,
  getId: (item: T) => string | number,
  item: T
) {
  try {
    const current = safeLoad<T>(key, max);
    const id = getId(item);
    const next = [item, ...current.filter((x) => getId(x) !== id)].slice(0, max);
    localStorage.setItem(key, JSON.stringify(next));
  } catch {
    // ignore
  }
}

export function RecentCombobox<T>({
  items,
  storageKey,

  selectedId: controlledSelectedId,
  onPick,

  placeholder = "Sélectionner…",
  searchPlaceholder = "Rechercher…",
  emptyLabel = "Aucun résultat.",
  recentsLabel = "Récemment consultés",
  listLabel = "Liste",
  recentsMax = 3,

  getId,
  getSearchValue,

  renderLeading,
  renderTitle,
  renderSubtitle,

  className,
  disabled,
}: {
  items: T[];
  storageKey: string;

  selectedId?: string | number | null;
  onPick: (item: T) => void;

  placeholder?: string;
  searchPlaceholder?: string;
  emptyLabel?: string;

  recentsLabel?: string;
  listLabel?: string;
  recentsMax?: number;

  getId: (item: T) => string | number;
  getSearchValue: (item: T) => string;

  renderLeading?: (item: T) => React.ReactNode;
  renderTitle: (item: T) => React.ReactNode;
  renderSubtitle?: (item: T) => React.ReactNode;

  className?: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = React.useState(false);
  const [internalSelectedId, setInternalSelectedId] = React.useState<
    string | number | null
  >(null);
  const [recents, setRecents] = React.useState<T[]>([]);

  const effectiveSelectedId = controlledSelectedId ?? internalSelectedId;

  React.useEffect(() => {
    setRecents(safeLoad<T>(storageKey, recentsMax));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedItem = React.useMemo(() => {
    if (effectiveSelectedId == null) return null;
    return items.find((x) => getId(x) === effectiveSelectedId) ?? null;
  }, [items, effectiveSelectedId, getId]);

  function handlePick(item: T) {
    safeSave(storageKey, recentsMax, getId, item);
    setRecents(safeLoad<T>(storageKey, recentsMax));

    if (controlledSelectedId == null) {
      setInternalSelectedId(getId(item));
    }

    setOpen(false);
    onPick(item);
  }

  return (
    <div className={cn("space-y-2", className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            disabled={disabled}
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between border-[color:var(--app-border)] bg-[color:var(--app-surface)] text-[color:var(--app-text)]"
          >
            <span className="truncate">
              {selectedItem ? renderTitle(selectedItem) : placeholder}
            </span>
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-60" />
          </Button>
        </PopoverTrigger>

        <PopoverContent
          align="start"
          sideOffset={4}
          className="w-[--radix-popover-trigger-width] p-0"
        >
          <Command>
            <CommandInput placeholder={searchPlaceholder} />

            <CommandList className="max-h-80">
              <CommandEmpty>{emptyLabel}</CommandEmpty>

              {recents.length > 0 ? (
                <>
                  <CommandGroup heading={recentsLabel}>
                    {recents.map((item) => {
                      const id = getId(item);

                      return (
                        <CommandItem
                          key={`recent-${String(id)}`}
                          value={getSearchValue(item)}
                          onSelect={() => handlePick(item)}
                          className="gap-3"
                        >
                          {renderLeading ? (
                            <span className="shrink-0">{renderLeading(item)}</span>
                          ) : null}

                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="truncate text-sm font-medium">
                                {renderTitle(item)}
                              </span>
                              <Clock className="h-3.5 w-3.5 opacity-60" />
                            </div>

                            {renderSubtitle ? (
                              <div className="truncate text-xs text-[color:var(--app-muted)]">
                                {renderSubtitle(item)}
                              </div>
                            ) : null}
                          </div>

                          <Check
                            className={cn(
                              "ml-2 h-4 w-4",
                              effectiveSelectedId === id ? "opacity-100" : "opacity-0"
                            )}
                          />
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                  <CommandSeparator />
                </>
              ) : null}

              <CommandGroup heading={listLabel}>
                {items.map((item) => {
                  const id = getId(item);

                  return (
                    <CommandItem
                      key={String(id)}
                      value={getSearchValue(item)}
                      onSelect={() => handlePick(item)}
                      className="gap-3"
                    >
                      {renderLeading ? (
                        <span className="shrink-0">{renderLeading(item)}</span>
                      ) : null}

                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium">
                          {renderTitle(item)}
                        </div>

                        {renderSubtitle ? (
                          <div className="truncate text-xs text-[color:var(--app-muted)]">
                            {renderSubtitle(item)}
                          </div>
                        ) : null}
                      </div>

                      <Check
                        className={cn(
                          "ml-2 h-4 w-4",
                          effectiveSelectedId === id ? "opacity-100" : "opacity-0"
                        )}
                      />
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
