"use client";

import type { User } from "@/types";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

export default function UserDetails({ user }: { user: User }) {
  return (
    <div className="space-y-4">
      <Card className="bg-muted/40">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{user.username}</CardTitle>
          <div className="mt-1 text-xs text-muted-foreground">Compte utilisateur</div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Informations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          <AdminDetailsRow label="ID" value={user.id} />
          <AdminDetailsRow label="Username" value={user.username} />
          <AdminDetailsRow
            label="Rôle"
            value={
              <Badge variant={user.role === "admin" ? "destructive" : "secondary"} className="capitalize">
                {user.role}
              </Badge>
            }
          />
          <AdminDetailsRow
            label="Statut"
            value={
              <Badge
                variant="secondary"
                className={user.is_active ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400" : ""}
              >
                {user.is_active ? "Actif" : "Inactif"}
              </Badge>
            }
            bordered={false}
          />
        </CardContent>
      </Card>
    </div>
  );
}
