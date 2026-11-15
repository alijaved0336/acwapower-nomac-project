import React from "react";
import { SiteId } from "../utils/pumpPerformanceData";
import { PumpHeatmapProvider } from "../context/pumpHeatmapContext";
import CompactPumpHeatmapLayout from "./CompactPumpHeatmapLayout";

interface PumpHeatmapLayoutProps {
  screenTitle: string;
  title: string;
  siteId: SiteId;
  showConditionalActions?: boolean;
}

const PumpHeatmapLayout: React.FC<PumpHeatmapLayoutProps> = ({
  title,
  siteId,
}) => {
  return (
    <PumpHeatmapProvider siteId={siteId} title={title}>
      <CompactPumpHeatmapLayout title={title} />
    </PumpHeatmapProvider>
  );
};

export default PumpHeatmapLayout;
