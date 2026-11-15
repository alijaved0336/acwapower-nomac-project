"use client";

import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapWaterfall } from "@/utils/chartMappers";
import {
  getWaterfallChartConfig,
  EChartsYAxisConfig,
} from "@/utils/chartConfig";

type EWaterfallChartProps = {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  yaxisOptions?: EChartsYAxisConfig[];
  onOpenYaxisModal?: () => void;
  showZoomControls?: boolean;
  showMenu?: boolean;
};

const EWaterfallChart: FC<EWaterfallChartProps> = ({
  columns,
  title = "",
  height = "50vh",
  width,
  loading = false,
  yaxisOptions,
  onOpenYaxisModal,
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { series, xAxis } = mapWaterfall(columns);
    return getWaterfallChartConfig(series, columns, xAxis, yaxisOptions);
  }, [columns, yaxisOptions]);

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

export default memo(EWaterfallChart);
