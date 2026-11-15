import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapXYSeries } from "@/utils/chartMappers";
import { getAreaChartConfig, EChartsYAxisConfig } from "@/utils/chartConfig";

type EAreaChartProps = {
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

const EAreaChart: FC<EAreaChartProps> = ({
  columns,
  title,
  height = "50vh",
  width,
  loading = false,
  yaxisOptions,
  onOpenYaxisModal,
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { series, xAxis } = mapXYSeries("line", columns);
    return getAreaChartConfig(series, columns, xAxis, yaxisOptions);
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

export default memo(EAreaChart);
