// src/components/common/charts/ELineChart.tsx
import React, { FC, memo, useMemo } from "react";
import EBaseChart from "./EBaseChart";
import { ColumnData } from "../../../types/analysis.types";
import { mapXYSeries } from "@/utils/chartMappers";
import {
  getLineBarScatterChartConfig,
  EChartsYAxisConfig,
} from "@/utils/themeChartConfig";
import useChartTheme from "../../../hooks/useChartTheme";

type ELineChartProps = {
  columns: ColumnData[];
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
  yAxisConfig?: EChartsYAxisConfig[];
  onOpenYaxisModal?: () => void;
  columnsLength?: number;
  showZoomControls?: boolean;
  showToolboxZoom?: boolean;
  showMenu?: boolean;
  customOptions?: any; // Allow custom options to override default config
};

const ELineChart: FC<ELineChartProps> = ({
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
  showToolboxZoom = true,
  customOptions,
}) => {
  const theme = useChartTheme();

  const options = useMemo(() => {
    const { series, xAxis } = mapXYSeries("line", columns);

    const baseConfig = getLineBarScatterChartConfig({
      series,
      columns,
      xAxis,
      yaxisOptions: yAxisConfig,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });

    // Merge custom options if provided
    if (customOptions) {
      const mergedConfig = {
        ...baseConfig,
        ...customOptions,
        // Deep merge tooltip if both exist
        tooltip: customOptions.tooltip || baseConfig.tooltip,
      };

      // Deep merge xAxis if both exist
      if (customOptions.xAxis && baseConfig.xAxis) {
        const baseXAxis = Array.isArray(baseConfig.xAxis)
          ? baseConfig.xAxis[0]
          : baseConfig.xAxis;
        const customXAxis = Array.isArray(customOptions.xAxis)
          ? customOptions.xAxis[0]
          : customOptions.xAxis;

        mergedConfig.xAxis = {
          ...baseXAxis,
          ...customXAxis,
        };
      }

      // Deep merge yAxis arrays if both exist
      if (customOptions.yAxis && baseConfig.yAxis) {
        const baseYAxis = Array.isArray(baseConfig.yAxis)
          ? baseConfig.yAxis
          : [baseConfig.yAxis];
        const customYAxis = Array.isArray(customOptions.yAxis)
          ? customOptions.yAxis
          : [customOptions.yAxis];

        mergedConfig.yAxis = baseYAxis.map((axis: any, index: number) => ({
          ...axis,
          ...(customYAxis[index] || {}),
        }));
      }

      // Deep merge legend if both exist
      if (customOptions.legend && baseConfig.legend) {
        let baseLegend: any;
        if (Array.isArray(baseConfig.legend)) {
          const legendArray = baseConfig.legend as any[];
          baseLegend = legendArray.length > 0 ? legendArray[0] : legendArray;
        } else {
          baseLegend = baseConfig.legend;
        }

        let customLegend: any;
        if (Array.isArray(customOptions.legend)) {
          const customLegendArray = customOptions.legend as any[];
          customLegend =
            customLegendArray.length > 0
              ? customLegendArray[0]
              : customLegendArray;
        } else {
          customLegend = customOptions.legend;
        }

        mergedConfig.legend = {
          ...baseLegend,
          ...customLegend,
          textStyle: {
            ...(baseLegend?.textStyle || {}),
            ...(customLegend?.textStyle || {}),
          },
        };
      }

      return mergedConfig;
    }

    return baseConfig;
  }, [columns, yAxisConfig, customOptions, theme]);

  return (
    <EBaseChart
      options={options}
      chartType="line"
      title={title}
      height={height}
      width={width}
      loading={loading}
      onOpenYaxisModal={onOpenYaxisModal}
      columnsLength={columnsLength ?? columns?.length ?? 0}
      showZoomControls={showZoomControls}
      showToolboxZoom={showToolboxZoom}
      showMenu={showMenu}
    />
  );
};

export default memo(ELineChart);
