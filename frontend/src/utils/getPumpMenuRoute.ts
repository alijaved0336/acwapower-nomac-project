/**
 * Helper function to get the route for pump menu items based on selected site
 * Returns the route for the default selected site's designated page
 */

import { SITE_ACTUAL_NAMES } from "./siteDisplayNames";

const SITE_TO_ROUTE_MAP = {
  UAQ: {
    performance: "/dashboard/pumps_performance/UAQ_Pumps",
    metrics: "/dashboard/pumpmetrics?site=UAQ",
    heatmap: "/dashboard/pump_heatmap/uaq-pumps",
    analysis: "/dashboard/pump_analysis?site=UAQ",
  },
  "Jubail-Jazlah": {
    performance: "/dashboard/pumps_performance/Jubail_Pumps",
    metrics: "/dashboard/pumpmetrics?site=Jubail-Jazlah",
    heatmap: "/dashboard/pump_heatmap/jubail-pumps",
    analysis: "/dashboard/pump_analysis?site=Jubail-Jazlah",
  },
  Rabigh3: {
    performance: "/dashboard/pumps_performance/Rabigh3_Pumps",
    metrics: "/dashboard/pumpmetrics?site=Rabigh3",
    heatmap: "/dashboard/pump_heatmap/rabigh3-pumps",
    analysis: "/dashboard/pump_analysis?site=Rabigh3",
  },
  STPC: {
    performance: "/dashboard/pumps_performance/UAQ_Pumps?site=STPC",
    metrics: "/dashboard/pumpmetrics?site=STPC",
    heatmap: "/dashboard/pump_heatmap/stpc-pumps",
    analysis: "/dashboard/pump_analysis?site=STPC",
  },
} as const;

type PumpMenuType = "performance" | "metrics" | "heatmap" | "analysis";

export const getPumpMenuRoute = (
  selectedSite: string | null,
  type: PumpMenuType,
  includeQueryParams: boolean = true
): string | null => {
  if (!selectedSite) {
    return null;
  }

  // Normalize site key - convert display name to actual site key if needed
  // The selectedSite from Redux might be a display name (e.g., "Jubail 3A IWP")
  // but we need the actual site key (e.g., "Jubail-Jazlah") for route mapping
  let normalizedSite = selectedSite;

  if (SITE_ACTUAL_NAMES[selectedSite]) {
    normalizedSite = SITE_ACTUAL_NAMES[selectedSite];
  } else if (selectedSite === "Jubail" || selectedSite === "Jubail 3A IWP") {
    // Handle legacy variations
    normalizedSite = "Jubail-Jazlah";
  }

  const siteRoute =
    SITE_TO_ROUTE_MAP[normalizedSite as keyof typeof SITE_TO_ROUTE_MAP];

  if (!siteRoute) {
    const matchingKey = Object.keys(SITE_TO_ROUTE_MAP).find(
      (key) =>
        key.toLowerCase().includes(selectedSite.toLowerCase()) ||
        selectedSite.toLowerCase().includes(key.toLowerCase())
    );

    if (matchingKey) {
      return SITE_TO_ROUTE_MAP[matchingKey as keyof typeof SITE_TO_ROUTE_MAP][
        type
      ];
    }

    return null;
  }

  let route: string = siteRoute[type];

  // For menu highlighting, we need base paths without query params
  // But for navigation, we include query params
  if (!includeQueryParams && route) {
    // Remove query params for pathname matching
    route = route.split("?")[0] as string;
  }

  return route;
};
