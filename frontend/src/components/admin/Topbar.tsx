import UserMenu from "@/components/admin/UserMenu";

export default function Topbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-end px-6">
        <UserMenu />
      </div>
    </header>
  );
}
