"use client";

import React, { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import PumpAnalysis from "@/components/features/PumpAnalysis/layouts/PumpAnalysis";
import CompactPumpAnalysis from "../../../../components/features/PumpAnalysis/layouts/compactPumpAnalysisLayout";
import { PumpAnalysisProvider } from "@/components/features/PumpAnalysis/context/pumpAnalysisContext";
import dayjs from "dayjs";

const PumpAnalysisPage: React.FC = () => {
  const searchParams = useSearchParams();
  const siteName = searchParams.get("site") || "UAQ";

  const initialDateRange: [dayjs.Dayjs, dayjs.Dayjs] = useMemo(
    () => [dayjs().subtract(7, "days"), dayjs()],
    []
  );

  return (
    <PumpAnalysisProvider
      key={siteName}
      siteName={siteName}
      initialDateRange={initialDateRange}
    >
      <CompactPumpAnalysis />
    </PumpAnalysisProvider>
  );
};

export default PumpAnalysisPage;
