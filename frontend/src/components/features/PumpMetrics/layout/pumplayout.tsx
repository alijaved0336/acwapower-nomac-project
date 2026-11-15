"use client";
import React from "react";
import Filters from "../filters/FiltersPumpMetrics";
import { PumpMetricsProvider } from "../context/pumpMetricsContext";
import Allchartslayout from "./Allchartslayout";
import { useSearchParams } from "next/navigation";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";

const PumpMetricsContent: React.FC<{ siteId: string }> = ({ siteId }) => {
  const displayName = getSiteDisplayName(siteId);

  return (
    <div
      className="relative"
      style={{
        height: "100vh",
        overflow: "hidden",
        // background: "linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Filters siteName={displayName} />

      <Allchartslayout siteName={displayName} />
    </div>
  );
};

const PumpMetrics: React.FC = () => {
  const searchParams = useSearchParams();
  // Use exact string, fallback to 'UAQ'
  const siteId = searchParams.get("site") || "UAQ";

  return (
    // Use key to force provider re-mount on site change
    <PumpMetricsProvider key={siteId} siteName={siteId}>
      <PumpMetricsContent siteId={siteId} />
    </PumpMetricsProvider>
  );
};

export default PumpMetrics;
