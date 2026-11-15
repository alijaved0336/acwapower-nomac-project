"use client";
import React, { memo, useEffect } from "react";
import SiteSelectionGuard from "@/components/auth/SiteSelectionGuard";
import { ChemicalDataProvider } from "@/components/features/dashboard/chemicals/context/ChemicalDataContext";
import AnalysisLayout from "@/components/features/dashboard/chemicals/layouts/AnalysisLayout";
import { useRouter } from "next/router";

const AnalysisPage: React.FC = memo(() => {
  // const router = useRouter();
  useEffect(() => {
    // console.log("AnalysisPage", router.pathname);
  }, []);
  return (
    <SiteSelectionGuard>
      <ChemicalDataProvider>
        <AnalysisLayout />
      </ChemicalDataProvider>
    </SiteSelectionGuard>
  );
});

AnalysisPage.displayName = "AnalysisPage";

export default AnalysisPage;
