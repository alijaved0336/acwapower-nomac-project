"use client";

import React, { useMemo, memo } from "react";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { ColumnData } from "@/types/analysis.types";
import { mapStackedBar } from "@/utils/chartMappers";
import {
  getStackedBarChartConfig,
  EChartsYAxisConfig,
} from "@/utils/themeChartConfig";
import { EStackedChartColorRecord } from "@/types";
import useChartTheme from "../../../../../hooks/useChartTheme";
import ErrorState from "../../../../common/ErrorState";
import Echart from "@/components/common/charts/Echart";
import { EChartsOption } from "echarts";

interface CompactStackedBarChartProps {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  seriesConfig?: EStackedChartColorRecord;
  yaxisOptions?: EChartsYAxisConfig[];
  onOpenYaxisModal?: () => void;
  showZoomControls?: boolean;
  showMenu?: boolean;
  error?: unknown;
  yAxisDisabled?: boolean;
  yAxisLabel?: string;
}

const CompactStackedBarChart: React.FC<CompactStackedBarChartProps> = ({
  columns,
  title = "",
  height = "100%",
  width,
  loading = false,
  seriesConfig,
  yaxisOptions,
  onOpenYaxisModal,
  showZoomControls = true,
  showMenu = true,
  error,
  yAxisDisabled,
  yAxisLabel,
}) => {
  const theme = useChartTheme();
  const options = useMemo(() => {
    // if (!columns || columns.length < 2) {
    //   return {
    //     xAxis: {
    //       type: "category",
    //       name: columns?.[0]?.columnName || "X",
    //       data: [],
    //     },
    //     yAxis: {},
    //     series: [],
    //   } as EChartsOption;
    // }

    const { categories, series } = mapStackedBar(columns, seriesConfig);

    return getStackedBarChartConfig(
      categories,
      series,
      columns,
      yaxisOptions,
      theme,
      yAxisLabel
    );
  }, [columns, seriesConfig, yaxisOptions, theme, yAxisLabel]);

  if (error) {
    return <ErrorState message="Error loading chart data" className="h-full" />;
  }

  return (
    <Echart
      options={options}
      title={title}
      loading={loading}
      chartType="bar"
      onOpenYaxisModal={onOpenYaxisModal}
      columnsLength={columns.length > 1 ? columns.length - 1 : 0}
      yAxisDisabled={yAxisDisabled}
    />
  );
};

export default memo(CompactStackedBarChart);
