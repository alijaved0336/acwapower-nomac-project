import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "@/types/analysis.types";
import { mapBoxplot } from "@/utils/chartMappers";
import { getBoxplotChartConfig, EChartsYAxisConfig } from "@/utils/chartConfig";

type EBoxPlotChartProps = {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  yAxisConfig?: EChartsYAxisConfig[];
  onOpenYaxisModal?: () => void;
  columnsLength?: number;
  showZoomControls?: boolean;
  showMenu?: boolean;
};

const EBoxPlotChart: FC<EBoxPlotChartProps> = ({
  columns,
  title = "",
  height = "50vh",
  width,
  loading = false,
  yAxisConfig = [],
  onOpenYaxisModal,
  columnsLength,
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { boxData, xAxis } = mapBoxplot(columns);
    return getBoxplotChartConfig(boxData, columns, yAxisConfig);
  }, [columns, yAxisConfig]);

  return (
    <EBaseChart
      options={options}
      chartType="boxplot"
      title={title}
      height={height}
      width={width}
      loading={loading}
      onOpenYaxisModal={onOpenYaxisModal}
      columnsLength={columnsLength ?? columns?.length ?? 0}
      showZoomControls={showZoomControls}
      showMenu={showMenu}
    />
  );
};

export default memo(EBoxPlotChart);
