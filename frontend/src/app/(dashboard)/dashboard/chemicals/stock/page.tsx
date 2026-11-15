"use client";
import React, { memo } from "react";
import SiteSelectionGuard from "@/components/auth/SiteSelectionGuard";
import SimpleStockLayout from "@/components/features/dashboard/chemicals/layouts/StockLayout";

const StockPage: React.FC = memo(() => {
  return (
    <SiteSelectionGuard>
      <SimpleStockLayout />
    </SiteSelectionGuard>
  );
});

StockPage.displayName = "StockPage";

export default StockPage;
