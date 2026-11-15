"use client";
import React, { Suspense } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { SITE_ID_MAP } from "@/components/features/dashboard/pump_heatmap/utils/pumpPerformanceData";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";

const PumpHeatmapLayout = dynamic(
  () =>
    import(
      "@/components/features/dashboard/pump_heatmap/layouts/PumpHeatmapLayout"
    )
);

const SLUG_CONFIG = {
  "jubail-pumps": {
    title: `${getSiteDisplayName(SITE_ID_MAP.JUBAIL)} Pumps Heatmap`,
    layoutTitle: `${getSiteDisplayName(SITE_ID_MAP.JUBAIL)} Pumps Heatmap`,
    siteId: SITE_ID_MAP.JUBAIL,
    showConditionalActions: false,
  },
  "rabigh3-pumps": {
    title: `${getSiteDisplayName(SITE_ID_MAP.RABIGH3)} Pumps Heatmap`,
    layoutTitle: `${getSiteDisplayName(SITE_ID_MAP.RABIGH3)} Pumps Heatmap`,
    siteId: SITE_ID_MAP.RABIGH3,
    showConditionalActions: false,
  },
  "uaq-pumps": {
    title: `${getSiteDisplayName(SITE_ID_MAP.UAQ)} Pumps Heatmap`,
    layoutTitle: `${getSiteDisplayName(SITE_ID_MAP.UAQ)} Pumps Heatmap`,
    siteId: SITE_ID_MAP.UAQ,
    showConditionalActions: true,
  },
  "stpc-pumps": {
    title: `${getSiteDisplayName(SITE_ID_MAP.STPC)} Pumps Heatmap`,
    layoutTitle: `${getSiteDisplayName(SITE_ID_MAP.STPC)} Pumps Heatmap`,
    siteId: SITE_ID_MAP.STPC,
    showConditionalActions: true,
  },
};

export default function PumpHeatmapPage() {
  const params = useParams();
  const slug = params.slug as keyof typeof SLUG_CONFIG;
  const config = SLUG_CONFIG[slug] || SLUG_CONFIG["jubail-pumps"];

  return (
    <ErrorBoundary>
      <Suspense>
        <PumpHeatmapLayout
          screenTitle={"Pump Heatmap"}
          title={config.layoutTitle}
          siteId={config.siteId}
          showConditionalActions={config.showConditionalActions}
        />
      </Suspense>
    </ErrorBoundary>
  );
}
