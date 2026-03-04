"use client";

import { useCallback, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import useSWRMutation from "swr/mutation";
import { toast } from "sonner";

import type { User, UpdateUserBody } from "@/types";
import { createUser, deleteUser, getUser, updateUser } from "@/services/users.service";

import type { ConfirmOptions } from "@/hooks/useConfirm";
import type { UserFormSubmitValues } from "@/features/users/user.form";

export type ConfirmFn = (opts: ConfirmOptions) => Promise<boolean>;

function useMutationAction<Arg, Data>(key: string, fn: (arg: Arg) => Promise<Data>) {
  return useSWRMutation<Data, Error, string, Arg>(key, async (_key, { arg }) => fn(arg));
}

export function useUsersCrud(opts: {
  confirm: ConfirmFn;
  refresh: () => void;
  setUsers: Dispatch<SetStateAction<User[]>>;
  includeInactive: boolean;
  currentUserId: number | null;
}) {
  const { confirm, refresh, setUsers, includeInactive, currentUserId } = opts;

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsUser, setDetailsUser] = useState<User | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const [editLoadingId, setEditLoadingId] = useState<number | null>(null);
  const [togglingIds, setTogglingIds] = useState<Set<number>>(new Set());

  const createMutation = useMutationAction("users:create", createUser);
  const updateMutation = useMutationAction(
    "users:update",
    ({ id, payload }: { id: number; payload: UpdateUserBody }) => updateUser(id, payload)
  );
  const deleteMutation = useMutationAction("users:delete", (id: number) => deleteUser(id));
  const toggleMutation = useMutationAction(
    "users:toggle",
    ({ id, is_active }: { id: number; is_active: boolean }) => updateUser(id, { is_active })
  );

  const submitting = createMutation.isMutating || updateMutation.isMutating;

  const closeView = useCallback(() => {
    setDetailsOpen(false);
  }, []);

  const openView = useCallback(
    async (u: User) => {
      if (viewLoadingId === u.id) return;

      setViewLoadingId(u.id);
      try {
        const full = await getUser(u.id);
        setDetailsUser(full);
        setDetailsOpen(true);
      } catch (e) {
        toast.error("Chargement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setViewLoadingId(null);
      }
    },
    [viewLoadingId]
  );

  const openCreate = useCallback(() => {
    setSelectedUser(null);
    setModalMode("create");
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (submitting) return;
    setModalOpen(false);
  }, [submitting]);

  const openEdit = useCallback(
    async (u: User) => {
      if (editLoadingId === u.id) return;

      setEditLoadingId(u.id);
      try {
        const full = await getUser(u.id);
        setSelectedUser(full);
        setModalMode("edit");
        setModalOpen(true);
      } catch (e) {
        toast.error("Chargement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setEditLoadingId(null);
      }
    },
    [editLoadingId]
  );

  const onDeleteUser = useCallback(
    async (u: User) => {
      if (currentUserId === u.id) {
        toast.error("Action interdite", {
          description: "Tu ne peux pas te supprimer toi-même.",
        });
        return;
      }

      const ok = await confirm({
        title: "Supprimer l’utilisateur",
        description: `Confirmer la suppression de ${u.username} ?`,
        confirmText: "Supprimer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      try {
        await deleteMutation.trigger(u.id);

        setUsers((prev) => {
          if (!includeInactive) {
            return prev.filter((x) => x.id !== u.id);
          }
          return prev.map((x) => (x.id === u.id ? { ...x, is_active: false } : x));
        });

        toast.success("Utilisateur supprimé", {
          description: `${u.username} a été désactivé.`,
        });
      } catch (e) {
        toast.error("Suppression impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      }
    },
    [confirm, currentUserId, deleteMutation, includeInactive, setUsers]
  );

  const toggleActive = useCallback(
    async (u: User) => {
      if (currentUserId === u.id) {
        toast.error("Action interdite", {
          description: "Tu ne peux pas modifier ton propre statut.",
        });
        return;
      }

      if (u.is_active) {
        const ok = await confirm({
          title: "Désactiver l’utilisateur",
          description: `Confirmer la désactivation de ${u.username} ?`,
          confirmText: "Désactiver",
          cancelText: "Annuler",
          variant: "danger",
        });
        if (!ok) return;
      }

      const nextActive = !u.is_active;
      setTogglingIds((prev) => new Set(prev).add(u.id));

      // optimistic update
      setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: nextActive } : x)));

      try {
        await toggleMutation.trigger({ id: u.id, is_active: nextActive });

        toast.success(u.is_active ? "Utilisateur désactivé" : "Utilisateur activé", {
          description: `${u.username} est maintenant ${nextActive ? "actif" : "inactif"}.`,
        });
      } catch (e) {
        // rollback
        setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: u.is_active } : x)));
        toast.error("Action impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setTogglingIds((prev) => {
          const next = new Set(prev);
          next.delete(u.id);
          return next;
        });
      }
    },
    [confirm, currentUserId, setUsers, toggleMutation]
  );

  const submitForm = useCallback(
    async (values: UserFormSubmitValues) => {
      try {
        if (modalMode === "create") {
          await createMutation.trigger({
            username: values.username,
            password: values.password ?? "",
            role: values.role,
            is_active: values.is_active,
          });
          toast.success("Utilisateur créé");
        } else {
          if (!selectedUser) return;

          const payload: UpdateUserBody = {
            username: values.username,
            role: values.role,
            is_active: values.is_active,
          };
          if (values.password) payload.password = values.password;

          await updateMutation.trigger({ id: selectedUser.id, payload });
          toast.success("Utilisateur mis à jour");
        }

        setModalOpen(false);
        refresh();
      } catch (e) {
        toast.error("Enregistrement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      }
    },
    [createMutation, modalMode, refresh, selectedUser, updateMutation]
  );

  return {
    detailsOpen,
    detailsUser,
    viewLoadingId,
    modalOpen,
    modalMode,
    selectedUser,
    submitting,
    editLoadingId,
    togglingIds,

    openCreate,
    openEdit,
    closeModal,
    deleteUser: onDeleteUser,
    toggleActive,
    submitForm,

    openView,
    closeView,
  };
}
