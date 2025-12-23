"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ErrorState";

export default function AgentsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // utile si tu ajoutes un système de log plus tard
    console.error(error);
  }, [error]);

  return (
    <main className="p-6">
      <ErrorState
        title="Impossible de charger les agents"
        message={error.message}
        onRetry={reset}
      />
    </main>
  );
}
