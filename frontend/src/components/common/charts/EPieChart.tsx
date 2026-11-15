import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapPieChart } from "@/utils/chartMappers";
import { getPieChartConfig } from "@/utils/chartConfig";

type EPieChartProps = {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  onOpenYaxisModal?: () => void;
  showZoomControls?: boolean;
  showMenu?: boolean;
};

const EPieChart: FC<EPieChartProps> = ({
  columns,
  title = "",
  height = "50vh",
  width,
  loading = false,
  onOpenYaxisModal,
  showZoomControls = false, // Pie charts typically don't need zoom
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const { series } = mapPieChart(columns);
    return getPieChartConfig(series, columns);
  }, [columns]);

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

export default memo(EPieChart);
