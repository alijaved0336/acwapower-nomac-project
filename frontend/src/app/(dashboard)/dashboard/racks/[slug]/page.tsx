"use client";
import { Suspense } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import SiteSelectionGuard from "@/components/auth/SiteSelectionGuard";
import { RackFiltersProvider } from "@/components/features/racks/context/RackFiltersContext";

const RacksInOperationLayout = dynamic(
  () => import("@/components/features/racks/layouts/RacksInOperationLayout")
);

const DaysSinceCIPLayout = dynamic(
  () => import("@/components/features/racks/layouts/CompactDaysSinceCIPLayout")
);

const SLUG_CONFIG = {
  operations: {
    component: RacksInOperationLayout,
  },
  "days-since-cip": {
    component: DaysSinceCIPLayout,
  },
};

export default function RacksPage() {
  const params = useParams();
  const slug = params.slug as keyof typeof SLUG_CONFIG;
  const config = SLUG_CONFIG[slug] || SLUG_CONFIG.operations;
  const LayoutComponent = config.component;

  return (
    <SiteSelectionGuard>
      <RackFiltersProvider slug={slug}>
        <Suspense>
          <LayoutComponent />
        </Suspense>
      </RackFiltersProvider>
    </SiteSelectionGuard>
  );
}
