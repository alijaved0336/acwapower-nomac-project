import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapHeatmap } from "@/utils/chartMappers";
import { getHeatMapConfig, HeatmapConfig } from "@/utils/chartConfig";

type EHeatmapChartProps = {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  heatmapConfig?: HeatmapConfig;
  onOpenYaxisModal?: () => void;
  showZoomControls?: boolean;
  showFullscreen?: boolean;
  showMenu?: boolean;
};

const EHeatmapChart: FC<EHeatmapChartProps> = ({
  columns,
  title = "",
  height = "50vh",
  width,
  loading = false,
  heatmapConfig,
  onOpenYaxisModal,
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { series, visualMap, xAxis, yAxis } = mapHeatmap(columns);
    return getHeatMapConfig(
      series,
      columns,
      xAxis,
      yAxis,
      visualMap,
      heatmapConfig
    );
  }, [columns, heatmapConfig]);

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

export default memo(EHeatmapChart);
