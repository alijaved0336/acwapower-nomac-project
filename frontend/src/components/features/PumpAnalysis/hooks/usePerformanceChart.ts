import { useMemo, useState, useCallback } from "react";
import { useGetPerformanceTrendQuery } from "@/store/api/pumpAnalysisApi";
import dayjs from "dayjs";
import type { GlobalToken } from "antd/es/theme/interface";
import {
  buildChartOptions,
  getEmptyChartOptions,
} from "../utils/performanceChartHelpers";

interface UsePerformanceChartProps {
  siteName: string;
  activePumpTab: string;
  pumpId: string;
  dateRange: any;
  token?: GlobalToken;
}

export const usePerformanceChart = ({
  siteName,
  activePumpTab,
  pumpId,
  dateRange,
  token,
}: UsePerformanceChartProps) => {
  const [speeds, setSpeeds] = useState<string[]>([]);
  const [metric1, setMetric1] = useState<string>("Flow_Measured");
  const [metric2, setMetric2] = useState<string>("");

  const shouldSkip = !siteName || !activePumpTab || !pumpId;

  const { data, isLoading, error, isFetching } = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: activePumpTab,
      pumpId,
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip: shouldSkip,
    }
  );

  const speedOptions = useMemo(() => {
    if (!data?.vsd_performance_data?.speed_groups) return [];
    return Object.keys(data?.vsd_performance_data?.speed_groups).map(
      (speed) => ({
        label: speed,
        value: speed,
      })
    );
  }, [data]);

  const metricOptions = useMemo(() => {
    if (!data?.column_data || !Array.isArray(data?.column_data)) {
      return [];
    }

    if (data.column_data.some((col) => col.columnName === "Flow_Measured")) {
      setMetric1("Flow_Measured");
    } else {
      setMetric1("Flow_Expected");
    }

    const options: { label: string; value: string }[] = [];
    const seenColumns = new Set<string>();

    data?.column_data.forEach((col: any) => {
      const colName = col.columnName;
      if (
        colName.toLowerCase() !== "timestamp" &&
        colName !== "Pump" &&
        colName !== "Pump_ID" &&
        colName !== "Speed" &&
        !seenColumns.has(colName)
      ) {
        seenColumns.add(colName);
        options.push({
          label: colName.replace(/_/g, " "),
          value: colName,
        });
      }
    });

    return options.sort((a, b) => a.label.localeCompare(b.label));
  }, [data]);

  const getChartResult = useCallback(
    (type: "Measured" | "Expected") => {
      const options = buildChartOptions(
        data,
        metric1,
        metric2,
        type,
        speeds,
        token
      );
      if (options) return { options, hasData: true };
      return {
        options: getEmptyChartOptions(metric1, metric2, token),
        hasData: false,
      };
    },
    [data, metric1, metric2, speeds, token]
  );

  return {
    data,
    isLoading: isLoading || isFetching,
    error,
    speeds,
    setSpeeds,
    metric1,
    setMetric1,
    metric2,
    setMetric2,
    speedOptions,
    metricOptions,
    getChartResult,
  };
};
