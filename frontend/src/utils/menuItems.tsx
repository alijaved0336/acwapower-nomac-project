import { MenuProps } from "antd";
import styles from "@/components/layouts/DashboardLayout/Sidebar.module.css";
import {
  AnalysisIcon,
  ChemicalIcon,
  DashboardIcon,
  RoleManagement,
  UserManagement,
} from "../assets/icons";
import PumpPerformanceIcon from "../assets/icons/pump_performance.svg";
import PumpMetricsIcon from "../assets/icons/pump_metrics.svg";
import RacksWeightedIcon from "../assets/icons/racks_weighted.svg";
import RacksNormalizedIcon from "../assets/icons/racks_normalized.svg";
import PumpHeatmapIcon from "../assets/icons/pump_heatmap.svg";
import PumpAnalysisIcon from "../assets/icons/pump_analysis_icon.svg";
import RORacksIcon from "../assets/icons/RO_Racks_icon.svg";
import ROPowerConsumptionIcon from "../assets/icons/ro_power_consumption.svg";
import RacksOperationIcon from "../assets/icons/Racks_operation_icon.svg";
import PlantOverviewIcon from "../assets/icons/plant_overview.svg";
import AlertOverviewIcon from "../assets/icons/alert_overview.svg";

// COMMENTED OUT: Old accordion implementation with children
// import { usePumpMenuChildren } from "../hooks/useMenu";
import { useAppSelector } from "../hooks";
import { cn } from "./cn";
import { getPumpMenuRoute } from "./getPumpMenuRoute";

type MenuItem = Required<MenuProps>["items"][number];
export const useMenuItems = (): MenuItem[] => {
  // Get selected site from Redux state
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  // COMMENTED OUT: Old accordion implementation
  // const menuChildren =
  //   (usePumpMenuChildren() as {
  //     pumpPerformanceChildren?: MenuItem[];
  //     pumpMetricsChildren?: MenuItem[];
  //     pumpHeatmapChildren?: MenuItem[];
  //     pumpAnalysisChildren?: MenuItem[];
  //   }) || {};
  // const pumpPerformanceChildren = menuChildren.pumpPerformanceChildren || [];
  // const pumpMetricsChildren = menuChildren.pumpMetricsChildren || [];
  // const pumpHeatmapChildren = menuChildren.pumpHeatmapChildren || [];
  // const pumpAnalysisChildren = menuChildren.pumpAnalysisChildren || [];
  const menuItems: MenuItem[] = [
    // 1. Overview
    {
      key: "/dashboard",
      label: "Overview",
      icon: <DashboardIcon className={styles.menuIcon} />,
    },
    // 2. Plant Overview
    {
      key: "/dashboard/plant-overview",
      label: "Plant Overview",
      icon: <PlantOverviewIcon className={styles.menuIcon} />,
    },
    // 3. RO Racks
    {
      key: "/dashboard/roracks",
      label: "RO Racks",
      icon: <RORacksIcon className={styles.menuIcon} />,
    },
    {
      key: "/dashboard/ro-power-consumption",
      label: "RO Power Consumption",
      icon: <ROPowerConsumptionIcon className={styles.menuIcon} />,
    },
    // 4. Pumps Performance
    // COMMENTED OUT: Old accordion implementation with children
    // {
    //   key: "/dashboard/pumps_performance",
    //   label: "Pumps Performance",
    //   icon: <PumpPerformanceIcon className={styles.menuIcon} />,
    //   children: pumpPerformanceChildren,
    // },
    // NEW: Direct link to selected site's performance page
    {
      key:
        getPumpMenuRoute(selectedSite, "performance") ||
        "/dashboard/pumps_performance",
      label: "Pumps Performance",
      icon: <PumpPerformanceIcon className={styles.menuIcon} />,
    },
    {
      key: "/dashboard/racks-normalized-performance",
      label: "Overall Racks Normalized Performance",
      icon: <RacksNormalizedIcon className={styles.menuIcon} />,
    },
  ];

  // 5. Pumps Analysis
  // COMMENTED OUT: Old accordion implementation with children
  // if (pumpAnalysisChildren?.length > 0) {
  //   menuItems.push({
  //     key: "/pump-analysis",
  //     label: "Pumps Analysis",
  //     icon: <PumpAnalysisIcon className={styles.menuIcon} />,
  //     children: pumpAnalysisChildren,
  //   });
  // }
  // NEW: Direct link to selected site's analysis page
  // Use base path (without query params) for menu key to match pathname for highlighting
  const analysisRoute =
    getPumpMenuRoute(selectedSite, "analysis", false) ||
    "/dashboard/pump_analysis";
  const analysisRouteWithParams =
    getPumpMenuRoute(selectedSite, "analysis", true) ||
    "/dashboard/pump_analysis";
  menuItems.push({
    key: analysisRoute, // Base path for highlighting
    label: "Pumps Analysis",
    icon: <PumpAnalysisIcon className={styles.menuIcon} />,
    // Store full route with params for navigation (using type assertion for custom property)
    route: analysisRouteWithParams,
  } as MenuItem & { route?: string });

  // 6. Pump Metrics
  // COMMENTED OUT: Old accordion implementation with children
  // if (pumpMetricsChildren?.length > 0) {
  //   menuItems.push({
  //     key: "/dashboard/pumpmetrics",
  //     label: "Pump Metrics",
  //     icon: <PumpMetricsIcon className={styles.menuIcon} />,
  //     children: pumpMetricsChildren,
  //   });
  // }
  // NEW: Direct link to selected site's metrics page
  // Use base path (without query params) for menu key to match pathname for highlighting
  const metricsRoute =
    getPumpMenuRoute(selectedSite, "metrics", false) ||
    "/dashboard/pumpmetrics";
  const metricsRouteWithParams =
    getPumpMenuRoute(selectedSite, "metrics", true) || "/dashboard/pumpmetrics";
  menuItems.push({
    key: metricsRoute, // Base path for highlighting
    label: "Pump Metrics",
    icon: <PumpMetricsIcon className={styles.menuIcon} />,
    // Store full route with params for navigation (using type assertion for custom property)
    route: metricsRouteWithParams,
  } as MenuItem & { route?: string });

  // 7. Pump Heatmaps
  // COMMENTED OUT: Old accordion implementation with children
  // if (pumpHeatmapChildren?.length > 0) {
  //   menuItems.push({
  //     key: "/dashboard/pump_heatmap",
  //     label: "Pump Heatmaps",
  //     icon: <PumpHeatmapIcon className={styles.menuIcon} />,
  //     children: pumpHeatmapChildren,
  //   });
  // }
  // NEW: Direct link to selected site's heatmap page
  menuItems.push({
    key: getPumpMenuRoute(selectedSite, "heatmap") || "/dashboard/pump_heatmap",
    label: "Pump Heatmaps",
    icon: <PumpHeatmapIcon className={styles.menuIcon} />,
  });

  // 8. Chemicals
  menuItems.push({
    key: "/chemicals",
    label: "Chemicals",
    icon: <ChemicalIcon className={styles.menuIcon} />,
    children: [
      {
        key: "/dashboard/chemicals/chemical-analysis",
        label: "Analysis",
      },
      {
        key: "/dashboard/chemicals/stock",
        label: "Stock",
      },
    ],
  });

  // Racks Weighted
  menuItems.push({
    key: "/dashboard/racks-weighted",
    label: "Racks Weighted",
    icon: <RacksWeightedIcon className={styles.menuIcon} />,
  });

  // Racks Operation
  menuItems.push({
    key: "/dashboard/racks",
    label: "Racks Operation",
    icon: <RacksOperationIcon className={styles.menuIcon} />,
    children: [
      {
        key: "/dashboard/racks/operations",
        label: "Racks Status and Availability",
      },
      {
        key: "/dashboard/racks/days-since-cip",
        label: "CIPs Performance",
      },
    ],
  });
  // Last Item. Analysis
  menuItems.push({
    key: "/dashboard/analysis",
    label: "Analysis",
    icon: <AnalysisIcon className={styles.menuIcon} />,
  });

  menuItems.push({
    key: "/dashboard/alerts-overview",
    label: "Alerts Overview",
    icon: <AlertOverviewIcon className={styles.menuIcon} />,
  });

  return menuItems;
};
