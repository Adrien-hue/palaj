"use client"

import { CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function TranchesCardHeader({
  title,
  count,
  disabled,
  addDisabled,
  onToggleAdd,
  listOpen,
  onToggleList,
}: {
  title: string
  count: number
  disabled: boolean
  addDisabled: boolean
  onToggleAdd: () => void
  listOpen: boolean
  onToggleList: () => void
}) {
  return (
    <CardHeader className="pb-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="truncate text-sm font-semibold">{title}</div>

            {disabled ? (
              <Badge variant="secondary" className="font-medium">
                Enregistrement…
              </Badge>
            ) : null}

            <Badge variant="secondary" className="font-medium tabular-nums">
              {count}
            </Badge>
          </div>

          <div className="mt-1 text-xs text-muted-foreground">
            Tranches relatives à ce poste.
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onToggleList}
            disabled={disabled}
          >
            {listOpen ? "Masquer la liste" : "Afficher la liste"}
          </Button>

          <Button
            type="button"
            size="sm"
            onClick={onToggleAdd}
            disabled={addDisabled}
          >
            + Ajouter
          </Button>
        </div>
      </div>
    </CardHeader>
  )
}
