"use client";

import React, { useMemo, useState, useEffect, useTransition } from "react";
import { useGetRoRacksDataQuery } from "@/store/api/roRacksApi";
import { useRoRacksContext } from "../context/RoRacksContext";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import { CompactChart } from "@/components/common";
import {
  EChartsYAxisConfig,
  getLineBarScatterChartConfig,
  HeatmapConfig,
} from "@/utils/themeChartConfig";
import { getChartData } from "../utils/roRacksUtils";
import { ColumnData } from "@/types/analysis.types";
import styles from "../styles/compactRoRacksChart.module.css";
import Spinner from "@/components/common/Spinner";
import useChartTheme from "../../../../hooks/useChartTheme";
import ErrorState from "../../../common/ErrorState";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import usePrepopulateYOptions from "@/hooks/usePrepopulatYOptions";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { mapXYSeries } from "@/utils/chartMappers";
import { isEmpty } from "lodash";
import { theme as antTheme } from "antd";
import Echart from "../../../common/charts/Echart";
import { useAppSelector } from "@/hooks";

interface CompactRoRacksChartProps {
  pass: "firstPass" | "secondPass";
  loading?: boolean;
}

/**
 * Maps Y-axis options based on series name:
 * - Permeate Flow metrics -> Left side (opposite: false)
 * - SEC metrics -> Right side (opposite: true)
 */
const mapYAxisBySeries = (
  options: EChartsYAxisConfig[]
): EChartsYAxisConfig[] => {
  if (!options || options.length === 0) return options;

  return options.map((option) => {
    const seriesName = option.seriesName?.toLowerCase() || "";

    // Check if this is a Permeate Flow metric
    if (seriesName.includes("permeate") && seriesName.includes("flow")) {
      return {
        ...option,
        opposite: false, // Left side
      };
    }

    // Check if this is a SEC metric
    if (seriesName.includes("sec")) {
      return {
        ...option,
        opposite: true, // Right side
      };
    }

    // Keep original position for other metrics
    return option;
  });
};

const CompactRoRacksChart: React.FC<CompactRoRacksChartProps> = ({
  pass,
  loading = false,
}) => {
  const { token } = antTheme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  const { selectedFilters, selectedSite } = useRoRacksContext();
  const site_name = selectedSite || selectedFilters?.plant;
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");

  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [yaxisOptions, setYaxisOptions] = useState<EChartsYAxisConfig[]>([]);
  const [, startTransition] = useTransition();
  const theme = useChartTheme();

  // Fetch data
  const { data, isLoading, error } = useGetRoRacksDataQuery(
    { site_name, selectedDate, pass },
    {
      selectFromResult: ({ data, isFetching, isLoading, error }) => ({
        data,
        isLoading: isFetching || isLoading,
        error,
      }),
      skip: !site_name || !selectedDate,
    }
  );

  // Get chart columns
  const columns: ColumnData[] = useMemo(() => {
    try {
      const result = getChartData(data);

      if (!Array.isArray(result)) {
        return [];
      }

      const validResult = result.filter(
        (column) =>
          column &&
          typeof column === "object" &&
          column.columnName &&
          Array.isArray(column.dataSource)
      );

      return validResult;
    } catch (error) {
      console.error("Error getting chart data:", error);
      return [];
    }
  }, [data]);

  // Get Y-axis configurator data
  const { numericColumns, ranges } = useYAxisConfigurator(columns || []);
  const defaultOptions = usePrepopulateYOptions(ranges);

  // Populate Y-axis options on first load and apply mapping
  useEffect(() => {
    if (!isEmpty(defaultOptions)) {
      const mappedOptions = mapYAxisBySeries(defaultOptions);
      setYaxisOptions(mappedOptions);
    }
  }, [defaultOptions]);

  // Chart configuration logic with mapped Y-axis options
  const options = useMemo(() => {
    const { series, xAxis } = mapXYSeries("line", columns);
    const mappedYAxisOptions = mapYAxisBySeries(yaxisOptions);

    return getLineBarScatterChartConfig({
      series,
      columns,
      xAxis,
      yaxisOptions: mappedYAxisOptions as EChartsYAxisConfig[],
      orientation: "vertical",
      yAxis: undefined,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });
  }, [columns, yaxisOptions, theme]);

  // Handle modal save with mapping
  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition(() => {
      if (Array.isArray(config)) {
        const mappedConfig = mapYAxisBySeries(config);
        setYaxisOptions(mappedConfig);
      }
    });
    setIsConfigModalOpen(false);
  };

  const showSpinner = loading || isLoading;

  if (error) {
    return <ErrorState message="Failed to load chart data" />;
  }

  return (
    <>
      {isConfigModalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={yaxisOptions}
          numericColumns={numericColumns}
          ranges={ranges}
          open={isConfigModalOpen}
          columns={columns || []}
          chartType="line"
          onCancel={() => setIsConfigModalOpen(false)}
          onSave={handleSave}
        />
      )}
      <div className={styles.container}>
        <div className={styles.chartWrapper}>
          <div className={styles.chartContent}>
            <Echart
              chartType="line"
              options={options}
              title=""
              // width="100%"
              // height="100%"
              loading={showSpinner}
              onOpenYaxisModal={() => setIsConfigModalOpen(true)}
              columnsLength={columns?.length ?? 0}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default CompactRoRacksChart;
