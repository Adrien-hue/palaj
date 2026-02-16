"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export function PosteDaySheetActions({
  isEditing,
  isDirty,
  isSaving,
  isDeleting,
  dayLabel,
  onStartEdit,
  onCancelEdit,
  onSave,
  onDeleteConfirmed,
}: {
  isEditing: boolean;
  isDirty: boolean;
  isSaving: boolean;
  isDeleting: boolean;

  dayLabel: string;

  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSave: () => Promise<unknown>;
  onDeleteConfirmed: () => Promise<unknown>;
}) {
  return (
    <div className="flex justify-between gap-2">
      {isEditing ? (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={onCancelEdit}
            disabled={isSaving || isDeleting}
          >
            Annuler
          </Button>

          <Button
            disabled={!isDirty || isSaving || isDeleting}
            onClick={onSave}
          >
            {isSaving ? "Enregistrement…" : "Enregistrer"}
          </Button>
        </div>
      ) : (
        <Button onClick={onStartEdit} disabled={isSaving || isDeleting}>
          Modifier
        </Button>
      )}

      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="destructive" disabled={isDeleting || isSaving}>
            {isDeleting ? "Suppression…" : "Supprimer"}
          </Button>
        </AlertDialogTrigger>

        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer la journée ?</AlertDialogTitle>
            <AlertDialogDescription>
              Cette action supprime les affectations du {dayLabel}.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting || isSaving}>
              Annuler
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={isDeleting || isSaving}
              onClick={onDeleteConfirmed}
            >
              {isDeleting ? "Suppression…" : "Confirmer"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
