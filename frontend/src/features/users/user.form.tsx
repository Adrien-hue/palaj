"use client";

import * as React from "react";
import { useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";

import type { User, UserRole } from "@/types";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type UserFormHandle = {
  submit: () => void;
};

type UserFormValues = {
  username: string;
  password: string;
  role: UserRole;
  is_active: boolean;
};

type UserFormSubmitValues = {
  username: string;
  password?: string;
  role: UserRole;
  is_active: boolean;
};

type UserFormProps = {
  mode: "create" | "edit";
  initialUser?: User | null;
  submitting: boolean;
  onSubmit: (values: UserFormSubmitValues) => Promise<void>;
};

const UserFormInner = React.forwardRef<UserFormHandle, UserFormProps>(function UserFormInner(
  { mode, initialUser, submitting, onSubmit },
  ref
) {
  const initial: UserFormValues = useMemo(
    () => ({
      username: initialUser?.username ?? "",
      password: "",
      role: initialUser?.role ?? "manager",
      is_active: initialUser?.is_active ?? true,
    }),
    [initialUser]
  );

  const [values, setValues] = useState<UserFormValues>(initial);
  const [error, setError] = useState<string | null>(null);

  const formRef = useRef<HTMLFormElement | null>(null);
  const usernameRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const t = setTimeout(() => usernameRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [mode, initialUser?.id]);

  function validate(v: UserFormValues) {
    const username = v.username.trim();
    if (!username) return "Le nom d’utilisateur est obligatoire.";
    if (username.length > 150) return "Le nom d’utilisateur doit faire au maximum 150 caractères.";

    const password = v.password.trim();
    if (mode === "create" && !password) return "Le mot de passe est obligatoire.";
    if (password && password.length < 8) return "Le mot de passe doit faire au minimum 8 caractères.";

    return null;
  }

  async function handleSubmit() {
    if (submitting) return;

    setError(null);
    const err = validate(values);
    if (err) {
      setError(err);
      return;
    }

    const payload: UserFormSubmitValues = {
      username: values.username.trim(),
      role: values.role,
      is_active: values.is_active,
    };

    const password = values.password.trim();
    if (password) payload.password = password;

    try {
      await onSubmit(payload);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }

  useImperativeHandle(
    ref,
    () => ({
      submit: () => formRef.current?.requestSubmit(),
    }),
    []
  );

  return (
    <form
      ref={formRef}
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}
      className="space-y-4"
    >
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Erreur</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="user-username">
          Nom d’utilisateur <span className="text-destructive">*</span>
        </Label>
        <Input
          id="user-username"
          ref={usernameRef}
          value={values.username}
          onChange={(e) => setValues((prev) => ({ ...prev, username: e.target.value }))}
          placeholder="admin"
          disabled={submitting}
          autoComplete="username"
          maxLength={150}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="user-password">
          Mot de passe {mode === "create" ? <span className="text-destructive">*</span> : null}
        </Label>
        <Input
          id="user-password"
          type="password"
          value={values.password}
          onChange={(e) => setValues((prev) => ({ ...prev, password: e.target.value }))}
          placeholder={mode === "create" ? "••••••••" : "Laisser vide pour conserver le mot de passe actuel."}
          disabled={submitting}
          autoComplete={mode === "create" ? "new-password" : "off"}
          required={mode === "create"}
          minLength={8}
        />
        <p className="text-xs text-muted-foreground">
          Minimum 8 caractères. Laisser vide pour conserver le mot de passe actuel.
        </p>
      </div>

      <div className="space-y-2">
        <Label>Rôle</Label>
        <Select
          value={values.role}
          onValueChange={(v: UserRole) => setValues((prev) => ({ ...prev, role: v }))}
          disabled={submitting}
        >
          <SelectTrigger>
            <SelectValue placeholder="Sélectionner un rôle" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="admin">admin</SelectItem>
            <SelectItem value="manager">manager</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between rounded-md border p-3">
        <div>
          <Label htmlFor="user-active">Utilisateur actif</Label>
          <p className="text-xs text-muted-foreground">Désactiver pour bloquer la connexion.</p>
        </div>
        <Switch
          id="user-active"
          checked={values.is_active}
          onCheckedChange={(checked) => setValues((prev) => ({ ...prev, is_active: checked }))}
          disabled={submitting}
        />
      </div>

      <p className="text-xs text-muted-foreground">
        <span className="text-destructive">*</span> Champs obligatoires
      </p>
    </form>
  );
});

export default React.forwardRef<UserFormHandle, UserFormProps>(function UserForm(props, ref) {
  const { mode, initialUser } = props;
  const formKey = `${mode}:${initialUser?.id ?? "new"}`;

  return <UserFormInner key={formKey} ref={ref} {...props} />;
});

export type { UserFormSubmitValues };
