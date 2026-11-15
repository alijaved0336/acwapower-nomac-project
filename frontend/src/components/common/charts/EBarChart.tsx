import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapXYSeries } from "@/utils/chartMappers";
import {
  getLineBarScatterChartConfig,
  EChartsYAxisConfig,
} from "@/utils/chartConfig";

type EBarChartProps = {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  orientation?: "vertical" | "horizontal";
  limit?: number;
  yaxisOptions?: EChartsYAxisConfig[];
  stack?: boolean | string;
  onOpenYaxisModal?: () => void;
  columnsLength?: number; // Added this prop
  showZoomControls?: boolean;
  showFullscreen?: boolean;
  showMenu?: boolean;
};

const EBarChart: FC<EBarChartProps> = ({
  columns,
  title,
  height = "50vh",
  width,
  loading = false,
  orientation = "vertical",
  limit,
  yaxisOptions,
  stack = false,
  onOpenYaxisModal,
  columnsLength, // Destructured here
  showZoomControls = true,
  showMenu = true,
}) => {
  const options = useMemo(() => {
    const result = mapXYSeries("bar", columns, orientation, limit);
    // eslint-disable-next-line prefer-const
    let { series, xAxis, yAxis } = result;

    if (stack) {
      series = series.map((s: any) => ({
        ...s,
        stack: typeof stack === "string" ? stack : "total",
      }));
    }

    return getLineBarScatterChartConfig({
      series,
      columns,
      xAxis,
      yaxisOptions: yaxisOptions as EChartsYAxisConfig[],
      orientation,
      yAxis,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
    });
  }, [columns, orientation, limit, yaxisOptions, stack]);

  return (
    <EBaseChart
      options={options}
      chartType="bar" // Added chartType prop
      title={title}
      width={width}
      loading={loading}
      onOpenYaxisModal={onOpenYaxisModal}
      columnsLength={columnsLength} // Pass it through to EBaseChart
      showZoomControls={showZoomControls}
      showMenu={showMenu}
    />
  );
};

export default memo(EBarChart);
