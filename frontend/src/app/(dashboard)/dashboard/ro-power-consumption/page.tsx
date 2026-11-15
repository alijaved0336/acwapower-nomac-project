"use client";

import SiteSelectionGuard from "@/components/auth/SiteSelectionGuard";
import CompactRoPowerConsumptionLayout from "@/components/features/ro-power-consumption/layout/CompactRoPowerConsumptionLayout";
import { RoPowerConsumptionProvider } from "@/components/features/ro-power-consumption/context/RoPowerConsumptionContext";

export default function Page() {
  return (
    <SiteSelectionGuard>
      <RoPowerConsumptionProvider>
        <CompactRoPowerConsumptionLayout />
      </RoPowerConsumptionProvider>
    </SiteSelectionGuard>
  );
}
