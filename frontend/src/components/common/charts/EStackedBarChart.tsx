"use client";

import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "@/types/analysis.types";
import { mapStackedBar } from "@/utils/chartMappers";
import {
  getStackedBarChartConfig,
  EChartsYAxisConfig,
} from "@/utils/chartConfig";
import { EStackedChartColorRecord } from "../../../types";

type EStackedBarChartProps = {
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
};

const EStackedBarChart: FC<EStackedBarChartProps> = ({
  columns,
  title = "",
  height = "50vh",
  width,
  loading = false,
  seriesConfig,
  yaxisOptions,
  onOpenYaxisModal,
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { categories, series } = mapStackedBar(columns, seriesConfig);
    return getStackedBarChartConfig(categories, series, columns, yaxisOptions);
  }, [columns, seriesConfig, yaxisOptions]);

  return (
    <EBaseChart
      options={options}
      title={title}
      height={height}
      width={width}
      loading={loading}
      onOpenYaxisModal={onOpenYaxisModal}
      showZoomControls={showZoomControls}
      showMenu={showMenu}
    />
  );
};

export default memo(EStackedBarChart);
