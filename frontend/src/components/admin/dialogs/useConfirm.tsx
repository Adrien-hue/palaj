"use client";

import { useCallback, useRef, useState } from "react";
import ConfirmDialog from "./ConfirmDialog";

type ConfirmOptions = {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "default";
};

export function useConfirm() {
  const resolverRef = useRef<((v: boolean) => void) | null>(null);

  const [state, setState] = useState<ConfirmOptions & { open: boolean }>({
    open: false,
    title: "",
  });

  const confirm = useCallback((opts: ConfirmOptions) => {
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
      setState({ open: true, ...opts });
    });
  }, []);

  const close = useCallback((value: boolean) => {
    setState((s) => ({ ...s, open: false }));
    resolverRef.current?.(value);
    resolverRef.current = null;
  }, []);

  const Confirm = useCallback(() => {
    return (
      <ConfirmDialog
        open={state.open}
        title={state.title}
        description={state.description}
        confirmText={state.confirmText}
        cancelText={state.cancelText}
        variant={state.variant}
        onCancel={() => close(false)}
        onConfirm={() => close(true)}
      />
    );
  }, [close, state]);

  return { confirm, ConfirmDialog: Confirm };
}
