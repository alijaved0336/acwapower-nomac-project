"use client";

import SiteSelectionGuard from "@/components/auth/SiteSelectionGuard";
import CompactRoRacksLayout from "@/components/features/ro-racks/layout/CompactRoRacksLayout";
import { RoRacksProvider } from "@/components/features/ro-racks/context/RoRacksContext";

export default function Page() {
  return (
    <SiteSelectionGuard>
      <RoRacksProvider>
        <CompactRoRacksLayout />
      </RoRacksProvider>
    </SiteSelectionGuard>
  );
}
