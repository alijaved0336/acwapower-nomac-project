import Select from "@/components/common/widgets/Select";
import { getLineBarScatterChartConfig } from "../../../../utils/themeChartConfig";
import { getColorBySpeedFactor } from "../../../../utils/helpers";
import { FC, useMemo, useState } from "react";
import { mapXYSeries } from "../../../../utils/chartMappers";
import {
  getAllSpeedGroupData,
  getPreferredMetricData,
  parseSpeedFactor,
  transformToColumnData,
} from "../utils/helper";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";

import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { useGetPumpMetricsQuery } from "@/store/api/pumpMetricsApi";
import dayjs from "dayjs";
import useChartTheme from "../../../../hooks/useChartTheme";
import { theme } from "antd";
import YAxisConfigurationModal, {
  YAxisConfig,
} from "../../PumpAnalysis/components/YAxisConfigurationModal";
import Echart from "../../../common/charts/Echart";

// Color palette for multiple pumps
const PUMP_COLORS = [
  "#5470c6",
  "#91cc75",
  "#fac858",
  "#ee6666",
  "#73c0de",
  "#3ba272",
  "#fc8452",
  "#9a60b4",
  "#ea7ccc",
];

// Metric units mapping
const METRIC_UNITS: Record<string, string> = {
  Flow: "m³/h",
  Pump_Flow: "m³/h",
  Efficiency: "%",
  SEC: "kWh/m³",
  Head: "m",
  Pump_Power: "kW",
};

// Type for dropdown options
type DropdownOption = {
  id: string;
  name: string;
};

type ChartProps = {
  title: string;
  defaultX: string;
  defaultY: string;
  loading?: boolean;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
};

export const KpiChart: FC<ChartProps> = ({
  title,
  defaultX,
  defaultY,
  loading = false,
  selectedPumpIds = [],
  selectedPumpCategories = [],
}) => {
  const {
    pumpMetrics,
    metricsLoading,
    metricsFetching,
    siteName,
    pumpsData,
    activePump,
    selectedFilters,
  } = usePumpMetricsContext();

  const chartTheme = useChartTheme();
  const { token } = theme.useToken();

  // Determine if we're in multi-pump mode
  const isMultiPumpMode = selectedPumpIds.length > 1;
  const effectivePumpIds = isMultiPumpMode
    ? selectedPumpIds.slice(0, 15) // Support up to 15 pumps
    : [activePump?.Pump_id || ""].filter(Boolean);

  const dateRange = selectedFilters.dateRange;
  const [fromDate, toDate] = useMemo(() => {
    if (!dateRange || !Array.isArray(dateRange)) return ["", ""];
    return [
      dateRange[0] ? dayjs(dateRange[0]).format("YYYY-MM-DD") : "",
      dateRange[1] ? dayjs(dateRange[1]).format("YYYY-MM-DD") : "",
    ];
  }, [dateRange]);

  // Make multiple API calls for multi-pump mode
  const pumpQuery0 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: isMultiPumpMode
        ? (selectedPumpCategories[0] || "").toLowerCase()
        : "",
      pump: isMultiPumpMode
        ? pumpsData?.[selectedPumpCategories[0] || ""]?.find(
            (p: any) => p.Pump_id === effectivePumpIds[0]
          )?.pump || ""
        : activePump?.pump || "",
      Pump_id: effectivePumpIds[0] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[0] ||
        (isMultiPumpMode && !selectedPumpCategories[0]) ||
        (!isMultiPumpMode && !activePump),
    }
  );

  const pumpQuery1 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[1] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[1] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[1]
        )?.pump || "",
      Pump_id: effectivePumpIds[1] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[1] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[1],
    }
  );

  const pumpQuery2 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[2] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[2] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[2]
        )?.pump || "",
      Pump_id: effectivePumpIds[2] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[2] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[2],
    }
  );

  const pumpQuery3 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[3] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[3] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[3]
        )?.pump || "",
      Pump_id: effectivePumpIds[3] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[3] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[3],
    }
  );

  const pumpQuery4 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[4] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[4] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[4]
        )?.pump || "",
      Pump_id: effectivePumpIds[4] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[4] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[4],
    }
  );

  const pumpQuery5 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[5] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[5] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[5]
        )?.pump || "",
      Pump_id: effectivePumpIds[5] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[5] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[5],
    }
  );

  const pumpQuery6 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[6] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[6] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[6]
        )?.pump || "",
      Pump_id: effectivePumpIds[6] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[6] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[6],
    }
  );

  const pumpQuery7 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[7] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[7] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[7]
        )?.pump || "",
      Pump_id: effectivePumpIds[7] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[7] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[7],
    }
  );

  const pumpQuery8 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[8] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[8] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[8]
        )?.pump || "",
      Pump_id: effectivePumpIds[8] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[8] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[8],
    }
  );

  const pumpQuery9 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[9] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[9] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[9]
        )?.pump || "",
      Pump_id: effectivePumpIds[9] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[9] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[9],
    }
  );

  const pumpQuery10 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[10] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[10] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[10]
        )?.pump || "",
      Pump_id: effectivePumpIds[10] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[10] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[10],
    }
  );

  const pumpQuery11 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[11] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[11] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[11]
        )?.pump || "",
      Pump_id: effectivePumpIds[11] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[11] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[11],
    }
  );

  const pumpQuery12 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[12] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[12] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[12]
        )?.pump || "",
      Pump_id: effectivePumpIds[12] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[12] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[12],
    }
  );

  const pumpQuery13 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[13] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[13] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[13]
        )?.pump || "",
      Pump_id: effectivePumpIds[13] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[13] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[13],
    }
  );

  const pumpQuery14 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[14] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[14] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[14]
        )?.pump || "",
      Pump_id: effectivePumpIds[14] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[14] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[14],
    }
  );

  const pumpQueries = [
    pumpQuery0,
    pumpQuery1,
    pumpQuery2,
    pumpQuery3,
    pumpQuery4,
    pumpQuery5,
    pumpQuery6,
    pumpQuery7,
    pumpQuery8,
    pumpQuery9,
    pumpQuery10,
    pumpQuery11,
    pumpQuery12,
    pumpQuery13,
    pumpQuery14,
  ].slice(0, effectivePumpIds.length);

  // Determine loading and error states
  const isLoading = isMultiPumpMode
    ? pumpQueries.some((q) => q.isLoading || q.isFetching)
    : metricsLoading || metricsFetching;

  // Use merged pump metrics for multi-pump mode or single pump metrics
  const mergedPumpMetrics = useMemo(() => {
    if (!isMultiPumpMode) {
      return pumpMetrics;
    }

    // For multi-pump mode, we'll use the first pump's structure but merge data
    // The chart will handle displaying multiple series
    return pumpQuery0.data || null;
  }, [isMultiPumpMode, pumpMetrics, pumpQuery0.data]);

  // Determine if this chart should have multiple y-axes
  const isMultiYAxisChart =
    title === "Shaft Power vs Expected" || title === "Head Actual vs Expected";
  const isThreeYAxisChart = title === "Efficiency Actual vs Expected";

  const [xMetric, setXMetric] = useState(defaultX);
  const [yMetric, setYMetric] = useState(defaultY);
  const [yMetric2, setYMetric2] = useState("Pump_Power");
  const [yMetric3, setYMetric3] = useState("Pump_Power");
  const [isYAxisModalVisible, setIsYAxisModalVisible] = useState(false);

  const [yAxisConfig, setYAxisConfig] = useState<YAxisConfig>(() => {
    // Initialize default config to ensure ticks appear correctly on first render
    if (title === "Efficiency Actual vs Expected") {
      return {
        yAxis1: { position: "left" },
        yAxis2: { position: "left" },
      } as YAxisConfig;
    } else if (
      title === "Shaft Power vs Expected" ||
      title === "Head Actual vs Expected"
    ) {
      return {
        yAxis1: { position: "left" },
        yAxis2: { position: "left" },
        yAxis3: { position: "left" },
      } as YAxisConfig;
    }
    return {} as YAxisConfig;
  });

  // Dropdown options with type
  const dropdownOptions: DropdownOption[] = useMemo(() => {
    const metrics = isMultiPumpMode ? mergedPumpMetrics : pumpMetrics;
    if (!metrics?.dropdown_data) return [];
    return metrics.dropdown_data.map((item: string) => ({
      id: item,
      name: item.replace(/_/g, " "),
    }));
  }, [pumpMetrics, mergedPumpMetrics, isMultiPumpMode]);

  const speedData = useMemo(() => {
    const metrics = isMultiPumpMode ? mergedPumpMetrics : pumpMetrics;
    if (!metrics?.vsd_performance_data?.speed_groups) return [];
    const data = metrics.vsd_performance_data.speed_groups;
    return Object.entries(data).map(([speedFactor, groupData]) => {
      const typedGroupData = groupData as any;
      return {
        speedFactor: parseFloat(speedFactor),
        ...typedGroupData,
      };
    });
  }, [pumpMetrics, mergedPumpMetrics, isMultiPumpMode]);

  const apiConfigs = useMemo(
    () => [
      {
        key: "pump_metrics",
        name: "Pump Metrics",
        data_availability_for_given_date: isMultiPumpMode
          ? pumpQueries.some((q) => q.data?.data_availability_for_given_date)
          : (pumpMetrics?.data_availability_for_given_date ?? true),
        from_date: isMultiPumpMode
          ? pumpQueries[0]?.data?.from_date
          : pumpMetrics?.from_date,
        to_date: isMultiPumpMode
          ? pumpQueries[0]?.data?.to_date
          : pumpMetrics?.to_date,
        isLoading: isLoading,
        isFetching: isLoading,
      },
    ],
    [
      isMultiPumpMode,
      pumpQueries,
      pumpMetrics?.data_availability_for_given_date,
      pumpMetrics?.from_date,
      pumpMetrics?.to_date,
      isLoading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const xColumn = useMemo(() => {
    const metrics = isMultiPumpMode ? mergedPumpMetrics : pumpMetrics;
    return getPreferredMetricData(metrics, xMetric);
  }, [pumpMetrics, mergedPumpMetrics, xMetric, isMultiPumpMode]);

  const yColumn = useMemo(() => {
    const metrics = isMultiPumpMode ? mergedPumpMetrics : pumpMetrics;
    return getPreferredMetricData(metrics, yMetric);
  }, [pumpMetrics, mergedPumpMetrics, yMetric, isMultiPumpMode]);

  const yColumn2 = useMemo(() => {
    if (!isMultiYAxisChart && !isThreeYAxisChart) return null;
    const metrics = isMultiPumpMode ? mergedPumpMetrics : pumpMetrics;
    return getPreferredMetricData(metrics, yMetric2);
  }, [
    isMultiYAxisChart,
    isThreeYAxisChart,
    pumpMetrics,
    mergedPumpMetrics,
    yMetric2,
    isMultiPumpMode,
  ]);

  const yColumn3 = useMemo(() => {
    if (!isMultiYAxisChart) return null;
    const metrics = isMultiPumpMode ? mergedPumpMetrics : pumpMetrics;
    return getPreferredMetricData(metrics, yMetric3);
  }, [
    isMultiYAxisChart,
    pumpMetrics,
    mergedPumpMetrics,
    yMetric3,
    isMultiPumpMode,
  ]);

  const xSpeedGroups = useMemo(
    () => getAllSpeedGroupData(speedData, xMetric),
    [speedData, xMetric]
  );

  const ySpeedGroups = useMemo(
    () => getAllSpeedGroupData(speedData, yMetric),
    [speedData, yMetric]
  );

  const chartData = useMemo(() => {
    if (!isMultiPumpMode) {
      const xData = transformToColumnData(xColumn);
      const yData = transformToColumnData(yColumn);
      if (!xData || !yData) return [];

      // For three-y-axis chart (Efficiency), return data for 2 y-axes
      if (isThreeYAxisChart && yColumn2) {
        const yData2 = transformToColumnData(yColumn2);
        if (yData2) {
          return [xData, yData, yData2];
        }
      }

      // For multi-y-axis chart, return data for all y-axes
      if (isMultiYAxisChart && yColumn2 && yColumn3) {
        const yData2 = transformToColumnData(yColumn2);
        const yData3 = transformToColumnData(yColumn3);
        if (yData2 && yData3) {
          return [xData, yData, yData2, yData3];
        }
      }

      return [xData, yData];
    }

    // For multi-pump mode, combine data from all pumps
    const allSeries: any[] = [];
    pumpQueries.forEach((query, pumpIndex) => {
      const pumpId = effectivePumpIds[pumpIndex];
      const data = query.data;
      if (!data) return;

      const xCol = getPreferredMetricData(data, xMetric);
      const yCol = getPreferredMetricData(data, yMetric);
      const xData = transformToColumnData(xCol);
      const yData = transformToColumnData(yCol);

      if (xData && yData) {
        allSeries.push({
          name: `Pump ${pumpId}`,
          type: "scatter" as const,
          data: xData.dataSource.map((xVal, i) => [xVal, yData.dataSource[i]]),
          symbolSize: 6,
          color: PUMP_COLORS[pumpIndex % PUMP_COLORS.length],
        });
      }
    });

    return allSeries;
  }, [
    isMultiPumpMode,
    isMultiYAxisChart,
    isThreeYAxisChart,
    xColumn,
    yColumn,
    yColumn2,
    yColumn3,
    pumpQueries,
    effectivePumpIds,
    xMetric,
    yMetric,
  ]);

  const speedGroupChartData = useMemo(() => {
    return xSpeedGroups
      .map((xGroup) => {
        const yGroup = ySpeedGroups.find(
          (y) => y.speedFactor === xGroup.speedFactor
        );

        if (!yGroup || xGroup.data.length === 0 || yGroup.data.length === 0) {
          return null;
        }

        const xData = transformToColumnData({
          columnName: xGroup.columnName,
          dataSource: xGroup.data,
        });
        const yData = transformToColumnData({
          columnName: yGroup.columnName,
          dataSource: yGroup.data,
        });

        if (!xData || !yData) return null;

        const speedFactorNum = parseSpeedFactor(xGroup.speedFactor.speedFactor);
        if (speedFactorNum === null) return null;

        return { speedFactor: speedFactorNum, xData, yData };
      })
      .filter((item): item is NonNullable<typeof item> => item !== null);
  }, [xSpeedGroups, ySpeedGroups]);

  const options = useMemo(() => {
    // Helper function to calculate automatic min/max for y-axes
    const calculateYAxisRange = (
      yAxisIndex: number,
      scatterData: any[],
      lineData: any[]
    ) => {
      const values: number[] = [];

      // Collect values from scatter series for this y-axis
      scatterData.forEach((series) => {
        if (series.yAxisIndex === yAxisIndex && Array.isArray(series.data)) {
          series.data.forEach((point: any) => {
            if (Array.isArray(point) && typeof point[1] === "number") {
              values.push(point[1]);
            }
          });
        }
      });

      // For the first y-axis, also include line series data (rated speed curves)
      if (yAxisIndex === 0) {
        lineData.forEach((series) => {
          if (Array.isArray(series.data)) {
            series.data.forEach((point: any) => {
              if (Array.isArray(point) && typeof point[1] === "number") {
                values.push(point[1]);
              }
            });
          }
        });
      }

      if (values.length === 0) {
        return { min: 0, max: 100 }; // Default range
      }

      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);

      // Ensure min is never negative
      const safeMin = Math.max(0, minValue);

      // Add 10% padding to the range for better visualization
      const range = maxValue - safeMin;
      const padding = range * 0.1;

      return {
        min: Math.max(0, Math.floor(safeMin - padding)),
        max: Math.ceil(maxValue + padding),
      };
    };

    const createLineSeriesFromSpeedGroups = (
      speedGroupData: typeof speedGroupChartData
    ) => {
      return speedGroupData.map(({ speedFactor, xData, yData }) => {
        const seriesData = xData.dataSource.map((xValue, i) => [
          xValue,
          yData.dataSource[i],
        ]);

        return {
          name: `Rated Speed ${speedFactor.toFixed(1)}x`,
          type: "line" as const,
          data: seriesData,
          smooth: true,
          showSymbol: false,
          color: getColorBySpeedFactor(speedFactor),
          lineStyle: {
            width: 2,
            type: "dashed" as const,
          },
          yAxisIndex: 0, // Line series always use first y-axis
        };
      });
    };

    let scatterSeries: any[] = [];
    if (isMultiPumpMode) {
      // For multi-pump mode, chartData is already series array
      scatterSeries =
        Array.isArray(chartData) && chartData.length > 0 && chartData[0].name
          ? chartData
          : [];
    } else if (isThreeYAxisChart && chartData.length === 3) {
      // For three-y-axis chart with single pump, create 2 scatter series
      const [xData, yData, yData2] = chartData;

      // Create scatter series for first y-axis
      scatterSeries.push({
        name: `${yMetric.replace(/_/g, " ")}`,
        type: "scatter" as const,
        data: xData.dataSource.map((xVal: any, i: number) => [
          xVal,
          yData.dataSource[i],
        ]),
        symbolSize: 6,
        yAxisIndex: 0,
      });

      // Create scatter series for second y-axis
      scatterSeries.push({
        name: `${yMetric2.replace(/_/g, " ")}`,
        type: "scatter" as const,
        data: xData.dataSource.map((xVal: any, i: number) => [
          xVal,
          yData2.dataSource[i],
        ]),
        symbolSize: 6,
        yAxisIndex: 1,
      });
    } else if (isMultiYAxisChart && chartData.length === 4) {
      // For multi-y-axis chart with single pump, create 3 scatter series
      const [xData, yData, yData2, yData3] = chartData;

      // Create scatter series for first y-axis
      scatterSeries.push({
        name: `${yMetric.replace(/_/g, " ")}`,
        type: "scatter" as const,
        data: xData.dataSource.map((xVal: any, i: number) => [
          xVal,
          yData.dataSource[i],
        ]),
        symbolSize: 6,
        yAxisIndex: 0,
      });

      // Create scatter series for second y-axis
      scatterSeries.push({
        name: `${yMetric2.replace(/_/g, " ")}`,
        type: "scatter" as const,
        data: xData.dataSource.map((xVal: any, i: number) => [
          xVal,
          yData2.dataSource[i],
        ]),
        symbolSize: 6,
        yAxisIndex: 1,
      });

      // Create scatter series for third y-axis
      scatterSeries.push({
        name: `${yMetric3.replace(/_/g, " ")}`,
        type: "scatter" as const,
        data: xData.dataSource.map((xVal: any, i: number) => [
          xVal,
          yData3.dataSource[i],
        ]),
        symbolSize: 6,
        yAxisIndex: 2,
      });
    } else {
      const result = mapXYSeries("scatter", chartData);
      scatterSeries = result.series;
    }

    const lineSeries = createLineSeriesFromSpeedGroups(speedGroupChartData);
    // Exclude trend lines for SEC chart
    const shouldShowTrendLines = !title.toLowerCase().includes("sec");
    const combinedSeries = shouldShowTrendLines
      ? [...scatterSeries, ...lineSeries]
      : scatterSeries;

    // Get xAxis from first scatter series or create default
    const baseXAxis =
      isMultiPumpMode && scatterSeries.length > 0
        ? { name: "", type: "value" as const }
        : mapXYSeries("scatter", chartData).xAxis;

    // Axis names with units - calculate these first
    const xAxisName =
      dropdownOptions.find((opt: DropdownOption) => opt.id === xMetric)?.name ||
      xMetric.replace(/_/g, " ");
    const xAxisWithUnit = `${xAxisName} (${METRIC_UNITS[xMetric] || ""})`;

    const yAxisName =
      dropdownOptions.find((opt: DropdownOption) => opt.id === yMetric)?.name ||
      yMetric.replace(/_/g, " ");
    const yAxisWithUnit = `${yAxisName} (${METRIC_UNITS[yMetric] || ""})`;

    // Create multiple y-axes if multi-y-axis chart - BEFORE creating chartConfig
    let finalYAxis: any = undefined;
    if (isThreeYAxisChart) {
      const yAxis2Name =
        dropdownOptions.find((opt: DropdownOption) => opt.id === yMetric2)
          ?.name || yMetric2.replace(/_/g, " ");
      const yAxis2WithUnit = `${yAxis2Name} (${METRIC_UNITS[yMetric2] || ""})`;

      // Get y-axis config for each axis
      const config1 = yAxisConfig["yAxis1"] || {};
      const config2 = yAxisConfig["yAxis2"] || {};

      // Calculate offsets based on positions
      let leftCount = 0;
      let rightCount = 0;
      const axes = [
        { config: config1, name: yAxisWithUnit, metric: yMetric },
        { config: config2, name: yAxis2WithUnit, metric: yMetric2 },
      ];

      finalYAxis = axes.map((axis, index) => {
        const position = axis.config.position || "left";
        const offset = position === "left" ? leftCount * 50 : rightCount * 50;
        if (position === "left") leftCount++;
        else rightCount++;

        // Calculate automatic range if not manually configured
        const autoRange = calculateYAxisRange(index, scatterSeries, lineSeries);
        const minValue =
          axis.config.min !== undefined ? axis.config.min : autoRange.min;
        const maxValue =
          axis.config.max !== undefined ? axis.config.max : autoRange.max;

        return {
          type: "value" as const,
          name: axis.name,
          nameLocation: "middle" as const,
          nameGap: 30,
          nameRotate: position === "right" ? -90 : 90,
          position: position,
          offset: offset,
          min: minValue,
          max: maxValue,
          nameTextStyle: {
            color: token.colorText,
            fontSize: 11,
            fontWeight: "bold" as const,
          },
          axisLine: {
            show: true,
            lineStyle: {
              color: axis.config.color || token.colorBorder,
            },
          },
          axisLabel: {
            show: true,
            color: token.colorText,
            fontSize: 10,
            margin: 4,
            formatter: (value: number) => {
              const absValue = Math.abs(value);
              if (absValue >= 1000) return `${(value / 1000).toFixed(1)}k`;
              if (absValue < 10) return value.toFixed(1); // Show 1 decimal for small ranges (like SEC)
              return value.toFixed(0); // Show integers for larger values
            },
          },
          splitLine: {
            show: index === 0,
          },
        };
      });
    } else if (isMultiYAxisChart) {
      const yAxis2Name =
        dropdownOptions.find((opt: DropdownOption) => opt.id === yMetric2)
          ?.name || yMetric2.replace(/_/g, " ");
      const yAxis2WithUnit = `${yAxis2Name} (${METRIC_UNITS[yMetric2] || ""})`;

      const yAxis3Name =
        dropdownOptions.find((opt: DropdownOption) => opt.id === yMetric3)
          ?.name || yMetric3.replace(/_/g, " ");
      const yAxis3WithUnit = `${yAxis3Name} (${METRIC_UNITS[yMetric3] || ""})`;

      // Get y-axis config for each axis
      const config1 = yAxisConfig["yAxis1"] || {};
      const config2 = yAxisConfig["yAxis2"] || {};
      const config3 = yAxisConfig["yAxis3"] || {};

      // Calculate offsets based on positions
      let leftCount = 0;
      let rightCount = 0;
      const axes = [
        { config: config1, name: yAxisWithUnit, metric: yMetric },
        { config: config2, name: yAxis2WithUnit, metric: yMetric2 },
        { config: config3, name: yAxis3WithUnit, metric: yMetric3 },
      ];

      finalYAxis = axes.map((axis, index) => {
        const position = axis.config.position || "left";
        const offset = position === "left" ? leftCount * 50 : rightCount * 50;
        if (position === "left") leftCount++;
        else rightCount++;

        // Calculate automatic range if not manually configured
        const autoRange = calculateYAxisRange(index, scatterSeries, lineSeries);
        const minValue =
          axis.config.min !== undefined ? axis.config.min : autoRange.min;
        const maxValue =
          axis.config.max !== undefined ? axis.config.max : autoRange.max;

        return {
          type: "value" as const,
          name: axis.name,
          nameLocation: "middle" as const,
          nameGap: 30,
          nameRotate: position === "right" ? -90 : 90,
          position: position,
          offset: offset,
          min: minValue,
          max: maxValue,
          nameTextStyle: {
            color: token.colorText,
            fontSize: 11,
            fontWeight: "bold" as const,
          },
          axisLine: {
            show: true,
            lineStyle: {
              color: axis.config.color || token.colorBorder,
            },
          },
          axisLabel: {
            show: true,
            color: token.colorText,
            fontSize: 10,
            margin: 4,
            formatter: (value: number) => {
              const absValue = Math.abs(value);
              if (absValue >= 1000) return `${(value / 1000).toFixed(1)}k`;
              if (absValue < 10) return value.toFixed(1); // Show 1 decimal for small ranges (like SEC)
              return value.toFixed(0); // Show integers for larger values
            },
          },
          splitLine: {
            show: index === 0,
          },
        };
      });
    }

    // Create chartConfig with the y-axis array already prepared
    const chartConfig = getLineBarScatterChartConfig({
      series: combinedSeries,
      columns: [],
      xAxis: baseXAxis,
      yAxis: finalYAxis, // Pass the y-axis config so yAxisCount is calculated correctly
      fontSizeMultiplier: 0.7,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme: chartTheme,
    });

    // For non-multi-axis charts, update finalYAxis from chartConfig and apply user config
    if (!isThreeYAxisChart && !isMultiYAxisChart) {
      const config1 = yAxisConfig["yAxis1"] || {};
      const position = config1.position || "left";

      finalYAxis = Array.isArray(chartConfig.yAxis)
        ? chartConfig.yAxis.map((axis, index) => ({
            ...axis,
            name: index === 0 ? yAxisWithUnit : axis.name,
            nameLocation: "middle" as const,
            nameGap: 30,
            nameRotate: position === "right" ? -90 : 90,
            position: position,
            ...(config1.min !== undefined && { min: config1.min }),
            ...(config1.max !== undefined && { max: config1.max }),
            nameTextStyle: {
              color: token.colorText,
              fontSize: 11,
              fontWeight: "bold" as const,
            },
            axisLine: {
              show: true,
              lineStyle: {
                color: config1.color || token.colorBorder,
              },
            },
          }))
        : {
            ...chartConfig.yAxis,
            name: yAxisWithUnit,
            nameLocation: "middle" as const,
            nameGap: 30,
            nameRotate: position === "right" ? -90 : 90,
            position: position,
            ...(config1.min !== undefined && { min: config1.min }),
            ...(config1.max !== undefined && { max: config1.max }),
            nameTextStyle: {
              color: token.colorText,
              fontSize: 11,
              fontWeight: "bold" as const,
            },
            axisLine: {
              show: true,
              lineStyle: {
                color: config1.color || token.colorBorder,
              },
            },
          };
    }

    // Calculate grid margins based on y-axis positions
    const calculateGridMargins = () => {
      if (!isThreeYAxisChart && !isMultiYAxisChart)
        return { left: 50, right: 20 };

      const configs = isThreeYAxisChart
        ? [yAxisConfig["yAxis1"] || {}, yAxisConfig["yAxis2"] || {}]
        : [
            yAxisConfig["yAxis1"] || {},
            yAxisConfig["yAxis2"] || {},
            yAxisConfig["yAxis3"] || {},
          ];

      const leftCount = configs.filter(
        (c) => (c.position || "left") === "left"
      ).length;
      const rightCount = configs.filter((c) => c.position === "right").length;

      return {
        left: Math.max(leftCount * 50, 60),
        right: Math.max(rightCount * 50, 20),
      };
    };
    const gridMargins = calculateGridMargins();

    return {
      ...chartConfig,
      xAxis: {
        ...chartConfig.xAxis,
        name: xAxisWithUnit,
        nameLocation: "middle" as const,
        nameGap: 30,
        nameTextStyle: {
          color: token.colorText,
          fontSize: 12,
          fontWeight: "bold" as const,
        },
      },
      yAxis: finalYAxis,
      grid: {
        ...chartConfig.grid,
        left: gridMargins.left,
        right: gridMargins.right,
        containLabel: false,
        bottom: 50,
      },
    };
  }, [
    chartData,
    speedGroupChartData,
    dropdownOptions,
    xMetric,
    yMetric,
    yMetric2,
    yMetric3,
    isMultiPumpMode,
    isMultiYAxisChart,
    isThreeYAxisChart,
    title,
    chartTheme,
    token.colorText,
    token.colorBorder,
    yAxisConfig,
  ]);

  const KPIChartFilters = () => {
    const hasMultipleYAxes = isMultiYAxisChart || isThreeYAxisChart;
    const maxWidthClass = hasMultipleYAxes ? "max-w-4xl" : "max-w-md";

    return (
      <div className={`flex w-full gap-8`}>
        <div className="grow">
          <Select
            value={xMetric}
            placeholder="Select X Axis"
            onChange={setXMetric}
            options={dropdownOptions}
            displayKey="name"
            valueKey="id"
            className="w-full text-sm"
            size="small"
          />
        </div>
        <div className="grow">
          <Select
            value={yMetric}
            placeholder="Select Y Axis"
            onChange={setYMetric}
            options={dropdownOptions}
            displayKey="name"
            valueKey="id"
            className="w-full text-sm"
            size="small"
          />
        </div>
        {isThreeYAxisChart && (
          <div className="grow">
            <Select
              value={yMetric2}
              placeholder="Select Y Axis 2"
              onChange={setYMetric2}
              options={dropdownOptions}
              displayKey="name"
              valueKey="id"
              className="w-full text-sm"
              size="small"
            />
          </div>
        )}
        {isMultiYAxisChart && (
          <>
            <div className="grow">
              <Select
                value={yMetric2}
                placeholder="Select Y Axis 2"
                onChange={setYMetric2}
                options={dropdownOptions}
                displayKey="name"
                valueKey="id"
                className="w-full text-sm"
                size="small"
              />
            </div>
            <div className="grow">
              <Select
                value={yMetric3}
                placeholder="Select Y Axis 3"
                onChange={setYMetric3}
                options={dropdownOptions}
                displayKey="name"
                valueKey="id"
                className="w-full text-sm"
                size="small"
              />
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <>
      <Echart
        options={options}
        chartType="scatter"
        title={title}
        onOpenYaxisModal={() => setIsYAxisModalVisible(true)}
        columnsLength={dropdownOptions.length}
        loading={loading || isLoading}
        secondHeader={true}
        secondHeaderContent={<KPIChartFilters />}
      />
      {/* <ECompactChart
        title={title}
        options={options}
        className="!rounded-xl"
        chartType="scatter"
        secondHeader={true}
        secondHeaderContent={<KPIChartFilters />}
        height="100%"
        width="100%"
        columnsLength={dropdownOptions.length}
        onOpenYaxisModal={() => setIsYAxisModalVisible(true)}
        loading={loading}
        yAxisDisabled={false}
        showYAxisConfig={true} // Enable Y-axis config for all charts
      /> */}
      <YAxisConfigurationModal
        visible={isYAxisModalVisible}
        onClose={() => setIsYAxisModalVisible(false)}
        onSave={(newConfig) => {
          setYAxisConfig(newConfig);
          setIsYAxisModalVisible(false);
        }}
        initialConfig={yAxisConfig}
        metrics={
          isThreeYAxisChart
            ? [
                { id: "yAxis1", label: yMetric.replace(/_/g, " ") },
                { id: "yAxis2", label: yMetric2.replace(/_/g, " ") },
              ]
            : isMultiYAxisChart
              ? [
                  { id: "yAxis1", label: yMetric.replace(/_/g, " ") },
                  { id: "yAxis2", label: yMetric2.replace(/_/g, " ") },
                  { id: "yAxis3", label: yMetric3.replace(/_/g, " ") },
                ]
              : [
                  { id: "yAxis1", label: yMetric.replace(/_/g, " ") }, // Single-axis charts
                ]
        }
      />
    </>
  );
};
