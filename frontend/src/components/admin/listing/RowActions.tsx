"use client";

import { Eye, Pencil, Trash2 } from "lucide-react";

export default function RowActions({
  onView,
  onEdit,
  onDelete,
}: {
  onView?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}) {
  return (
    <div className="flex gap-2">
      {onView && (
        <button
          title="Voir"
          className="
            inline-flex h-8 w-8 items-center justify-center rounded-full
            bg-zinc-100 text-zinc-700
            hover:bg-zinc-200
            focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2
            transition
          "
          onClick={onView}
        >
          <Eye className="h-4 w-4" />
        </button>
      )}
      {onEdit && (
        <button
          title="Éditer"
          className="
            inline-flex h-8 w-8 items-center justify-center rounded-full
            bg-zinc-100 text-zinc-700
            hover:bg-zinc-200
            focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2
            transition
          "
          onClick={onEdit}
        >
          <Pencil className="h-4 w-4" />
        </button>
      )}
      {onDelete && (
        <button
          title="Supprimer"
          className="
            inline-flex items-center justify-center
            h-8 w-8 rounded-full
            bg-red-600 text-white
            hover:bg-red-700
            active:bg-red-800
            focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2
            transition
          "
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
