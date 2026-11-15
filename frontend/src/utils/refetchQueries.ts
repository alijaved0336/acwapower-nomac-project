import { store } from "@/store/store";
import { slices } from "@/store/store";

const ROUTE_TO_APIS: Record<
  string,
  { reducerPath: string; tagTypes: string[] }[]
> = {
  "/dashboard/ro-power-consumption": [
    {
      reducerPath: "roPowerConsumptionApi",
      tagTypes: [
        "RoPowerConsumptionChart",
        "AvgWeightedHeatmap",
        "WeightedHeatmap",
      ],
    },
  ],

  "/dashboard/pump_analysis": [
    {
      reducerPath: "pumpAnalysisApi",
      tagTypes: ["PumpAnalysis", "OperationalTrend", "PerformanceTrend"],
    },
  ],

  "/dashboard/racks-weighted": [
    {
      reducerPath: "racksWeightedApi",
      tagTypes: ["RacksWeighted", "ROSummary", "Conductivities", "Rack"],
    },
  ],

  "/dashboard/chemicals/chemical-analysis": [
    {
      reducerPath: "chemicalApi",
      tagTypes: ["ChemicalFilter", "ChemicalData", "ChemicalStock"],
    },
  ],

  "/dashboard/chemicals/stock": [
    {
      reducerPath: "chemicalApi",
      tagTypes: ["ChemicalStock"],
    },
  ],

  "/dashboard/alerts-overview": [
    {
      reducerPath: "alertsOverviewApi",
      tagTypes: ["AlertsOverview", "AlertsGraph", "AssetHistory"],
    },
  ],

  "/dashboard/racks/days-since-cip": [
    {
      reducerPath: "rackApi",
      tagTypes: [
        "Racks",
        "CIP",
        "Flushing",
        "MembraneTable",
        "KPI",
        "Percentage",
      ],
    },
  ],
  "/dashboard/racks/racks-in-operation": [
    {
      reducerPath: "rackApi",
      tagTypes: [
        "Racks",
        "CIP",
        "Flushing",
        "MembraneTable",
        "KPI",
        "Percentage",
      ],
    },
  ],
  "/dashboard/racks/operations": [
    {
      reducerPath: "rackApi",
      tagTypes: [
        "Racks",
        "CIP",
        "Flushing",
        "MembraneTable",
        "KPI",
        "Percentage",
      ],
    },
  ],

  "/dashboard/analysis": [
    {
      reducerPath: "analysisApi",
      tagTypes: [
        "Analysis",
        "AnalysisTemplate",
        "AnalysisWidgets",
        "Widget",
        "Site",
        "Table",
        "Column",
        "Rack",
      ],
    },
  ],

  "/dashboard": [
    {
      reducerPath: "energyApi",
      tagTypes: [
        "Group",
        "Plant",
        "Cluster",
        "KPI",
        "DailyDispatch",
        "MapData",
      ],
    },
  ],

  "/dashboard/plant-overview": [
    {
      reducerPath: "plantOverviewApi",
      tagTypes: [
        "PlantOverview",
        "AreaFilter",
        "SectionOne",
        "ProcessOverview",
        "OperationalStatus",
        "DailyReport",
      ],
    },
    {
      reducerPath: "energyApi",
      tagTypes: ["MapData"],
    },
  ],

  "/dashboard/roracks": [
    {
      reducerPath: "roRacksApi",
      tagTypes: ["RoRacksData", "RoRacksTable", "RoOperationalStatus"],
    },
  ],

  "/dashboard/pumps_performance": [
    {
      reducerPath: "pumpsApi",
      tagTypes: [
        "PumpCategory",
        "ActionsOverview",
        "PumpFilter",
        "CardsData",
        "PumpKPIs",
      ],
    },
  ],

  "/dashboard/racks-normalized-performance": [
    {
      reducerPath: "racksNormalizedApi",
      tagTypes: ["NormalizedData"],
    },
  ],

  "/dashboard/pumpmetrics": [
    {
      reducerPath: "pumpMetricsApi",
      tagTypes: ["PumpMetrics"],
    },
  ],

  "/dashboard/pump_heatmap": [
    {
      reducerPath: "heatMapPumpApi",
      tagTypes: ["PumpCategories", "PumpHeatmapData"],
    },
  ],
};

const getCurrentRoute = (): string => {
  if (typeof window === "undefined") return "";
  const pathname = window.location.pathname;
  return pathname.replace(/\/$/, "") || "/";
};

const findMatchingRoute = (pathname: string): string | null => {
  if (ROUTE_TO_APIS[pathname]) {
    return pathname;
  }

  const sortedRoutes = Object.keys(ROUTE_TO_APIS).sort(
    (a, b) => b.length - a.length
  );
  for (const route of sortedRoutes) {
    if (pathname.startsWith(route)) {
      return route;
    }
  }

  return null;
};

export const refetchAllActiveQueries = () => {
  const currentRoute = getCurrentRoute();
  const matchingRoute = findMatchingRoute(currentRoute);

  if (!matchingRoute) {
    console.warn(`No API mapping found for route: ${currentRoute}`);
    return;
  }

  const apiConfigs = ROUTE_TO_APIS[matchingRoute];

  apiConfigs.forEach(({ reducerPath, tagTypes }) => {
    try {
      const api = (slices as Record<string, any>)[reducerPath];
      if (!api) {
        console.warn(`API not found: ${reducerPath}`);
        return;
      }

      if (tagTypes.length > 0 && api.util?.invalidateTags) {
        const tagsToInvalidate = tagTypes.map((tagType) => ({
          type: tagType,
        }));
        store.dispatch(api.util.invalidateTags(tagsToInvalidate));
      }

      const state = store.getState();
      const apiState = (state as any)[reducerPath];

      if (apiState?.queries) {
        Object.entries(apiState.queries).forEach(
          ([queryKey, queryState]: [string, any]) => {
            try {
              if (
                queryState?.status === "fulfilled" &&
                queryState.originalArgs !== undefined
              ) {
                const match = queryKey.match(/^(.+)\(/);
                if (match) {
                  const endpointName = match[1];
                  const endpoints = api.endpoints as Record<string, any>;
                  const endpoint = endpoints[endpointName];

                  if (endpoint?.initiate) {
                    store.dispatch(
                      endpoint.initiate(queryState.originalArgs, {
                        forceRefetch: true,
                        subscribe: false,
                      } as any)
                    );
                  }
                }
              }
            } catch {
              // Continue with other queries
            }
          }
        );
      }
    } catch (error) {
      console.warn(`Failed to refetch queries for ${reducerPath}:`, error);
    }
  });
};
