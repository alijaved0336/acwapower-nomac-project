import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapXYSeries } from "@/utils/chartMappers";
import {
  getLineBarScatterChartConfig,
  EChartsYAxisConfig,
} from "@/utils/chartConfig";

type EScatterChartProps = {
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

const EScatterChart: FC<EScatterChartProps> = ({
  columns,
  title = "",
  height = "50vh",
  width,
  loading = false,
  yaxisOptions = [],
  onOpenYaxisModal,
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { series, xAxis } = mapXYSeries("scatter", columns);
    return getLineBarScatterChartConfig({
      series,
      columns,
      xAxis,
      yaxisOptions: yaxisOptions as EChartsYAxisConfig[],
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
    });
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

export default memo(EScatterChart);
