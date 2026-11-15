"use client";

import SiteSelectionGuard from "@/components/auth/SiteSelectionGuard";
import RacksWeighted from "@/components/features/racks-weighted/components/RacksWeighted";

export default function Page() {
  return (
    <SiteSelectionGuard>
      <RacksWeighted />
    </SiteSelectionGuard>
  );
}
