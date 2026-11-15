import { useMemo } from "react";
import { MenuProps } from "antd";
import { extractSitesFromClusters } from "../utils/helpers";
import { getSiteDisplayName } from "../utils/siteDisplayNames";
import { useAppSelector } from ".";

type MenuItem = Required<MenuProps>["items"][number];

const SITE_MAPPINGS = {
  UAQ: {
    siteKey: "UAQ",
    performance: "/dashboard/pumps_performance/UAQ_Pumps?site=UAQ",
    metrics: "/dashboard/pumpmetrics?site=UAQ",
    heatmap: "/dashboard/pump_heatmap/uaq-pumps",
    analysis: "/dashboard/pump_analysis?site=UAQ",
    label: `${getSiteDisplayName("UAQ")} Pumps`,
  },
  "Jubail-Jazlah": {
    siteKey: "Jubail-Jazlah",
    performance: "/dashboard/pumps_performance/UAQ_Pumps?site=Jubail-Jazlah",
    metrics: "/dashboard/pumpmetrics?site=Jubail-Jazlah",
    heatmap: "/dashboard/pump_heatmap/jubail-pumps",
    analysis: "/dashboard/pump_analysis?site=Jubail-Jazlah",
    label: `${getSiteDisplayName("Jubail-Jazlah")} Pumps`,
  },
  Rabigh3: {
    siteKey: "Rabigh3",
    performance: "/dashboard/pumps_performance/UAQ_Pumps?site=Rabigh3",
    metrics: "/dashboard/pumpmetrics?site=Rabigh3",
    heatmap: "/dashboard/pump_heatmap/rabigh3-pumps",
    analysis: "/dashboard/pump_analysis?site=Rabigh3",
    label: `${getSiteDisplayName("Rabigh3")} Pumps`,
  },
  STPC: {
    siteKey: "STPC",
    performance: "/dashboard/pumps_performance/UAQ_Pumps?site=STPC",
    metrics: "/dashboard/pumpmetrics?site=STPC",
    heatmap: "/dashboard/pump_heatmap/stpc-pumps",
    analysis: "/dashboard/pump_analysis?site=STPC",
    label: `${getSiteDisplayName("STPC")} Pumps`,
  },
} as const;

// 🔧 Helper to build pump menu children based on site access
const buildPumpMenuChildren = (
  sites: string[],
  type: "performance" | "metrics" | "heatmap" | "analysis"
): MenuItem[] => {
  return Object.values(SITE_MAPPINGS)
    .filter((site) => sites.includes(site.siteKey))
    .map((site) => ({
      key: site[type],
      label: site.label,
    }));
};

export const usePumpMenuChildren = () => {
  const user = useAppSelector((state) => state.auth.user);

  const pumpChildren = useMemo(() => {
    const sites = extractSitesFromClusters(user?.role?.clusters || []);

    return {
      pumpPerformanceChildren: buildPumpMenuChildren(sites, "performance"),
      pumpMetricsChildren: buildPumpMenuChildren(sites, "metrics"),
      pumpHeatmapChildren: buildPumpMenuChildren(sites, "heatmap"),
      pumpAnalysisChildren: buildPumpMenuChildren(sites, "analysis"),
    };
  }, [user]);

  return pumpChildren;
};
