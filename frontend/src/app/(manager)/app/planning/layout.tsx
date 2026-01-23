import { PlanningTabsBar } from "@/features/planning-common/components/PlanningTabsBar";

export default function PlanningLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="sticky top-14 z-40">
        <PlanningTabsBar />
      </div>

      <div className="mx-auto w-full max-w-[1600px] px-6 py-6">
        {children}
      </div>
    </>
  );
}
