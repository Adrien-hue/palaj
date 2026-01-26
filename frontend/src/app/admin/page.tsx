import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminHomePage() {
  return (
    <Card className="rounded-2xl shadow-sm">
      <CardHeader>
        <CardTitle>PALAJ — Admin</CardTitle>
      </CardHeader>
      <CardContent className="text-muted-foreground">
        Layout admin OK
      </CardContent>
    </Card>
  );
}
