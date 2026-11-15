import React, {
  FC,
  useState,
  useMemo,
  useTransition,
  forwardRef,
  useImperativeHandle,
  useEffect,
} from "react";
import { theme } from "antd";
import ECompactChart from "@/components/common/charts/ECompactChart";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";
import { ColumnData } from "@/types/analysis.types";
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";

import { DailyDispatchDataPoint } from "../../../../../store/api/energyApi";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { Plant } from "../../../../../types/energy.types";
import useChartTheme from "../../../../../hooks/useChartTheme";

import Echart from "../../../../common/charts/Echart";

type Props = {
  loading?: boolean;
  fetching?: boolean;
  data: DailyDispatchDataPoint[];
  selectedPlants?: Plant[];
  selectedPlant?: string;
  selectedCluster?: string;
};

// The methods we want to expose to parent
export interface DailyDispatchLineChartRef {
  resetYAxisConfig: () => void;
}

const DailyDispatchLineChart = forwardRef<DailyDispatchLineChartRef, Props>(
  (
    {
      loading = false,
      fetching = false,
      data,
      selectedPlants = [],
      selectedPlant = "All Plants",
      selectedCluster = "All Clusters",
    },
    ref
  ) => {
    const [modalOpen, setModalOpen] = useState(false);
    const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[] | null>(
      null
    );
    const [isPending, startTransition] = useTransition();

    const chartTheme = useChartTheme();

    const lineData: ColumnData[] = useMemo(() => {
      if (!data) return [];
      const dataArray = Array.isArray(data) ? data : [];
      if (dataArray.length === 0) return [];
      return (dataArray as any as ColumnData[]).map((col) => {
        const siteName = col.siteName || col.columnName || "";
        const displayName = getSiteDisplayName(siteName);
        return {
          ...col,
          siteName,
          displayName,
          columnName: displayName || col.columnName,
        };
      });
    }, [data]);

    const { numericColumns, ranges } = useYAxisConfigurator(lineData);

    // Generate default y-axis configs: all on left
    const defaultYAxisConfig = useMemo(() => {
      if (numericColumns.length === 0) return [];
      const seriesNames = numericColumns.map((col) => col.columnName);
      return seriesNames.slice(0, 4).map((seriesName) => ({
        seriesName,
        show: true,
        opposite: false, // All on left
        axisLabel: { formatter: (val: number) => val.toFixed(2) },
        title: { text: seriesName },
        axisBorder: { show: true, color: "#888" },
        axisTicks: { show: true, color: "#888", width: 1 },
        tooltip: { enabled: true },
      }));
    }, [numericColumns]);

    // Set default configuration when columns are available and no manual config exists
    useEffect(() => {
      if (defaultYAxisConfig.length > 0 && yAxisConfig === null) {
        setYAxisConfig(defaultYAxisConfig);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [defaultYAxisConfig]);

    // Use default config if no manual config is set, otherwise use manual config
    const effectiveYAxisConfig = useMemo(() => {
      if (yAxisConfig === null) {
        return defaultYAxisConfig;
      }
      return yAxisConfig;
    }, [yAxisConfig, defaultYAxisConfig]);

    const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
      startTransition(() => {
        if (Array.isArray(config)) {
          setYAxisConfig(config);
        }
      });
      setModalOpen(false);
    };

    const chartOptions = useMemo(() => {
      const { series, xAxis } = mapXYSeries(
        "line",
        lineData ?? [],
        "vertical",
        undefined,
        true
      );
      const updatedSeries = series.map(
        (s: { name?: string; columnName?: string; [key: string]: any }) => ({
          ...s,
          name: getSiteDisplayName(s.name || s.columnName || ""),
        })
      );
      return getLineBarScatterChartConfig({
        series: updatedSeries,
        columns: lineData,
        xAxis,
        yaxisOptions: effectiveYAxisConfig,
        orientation: "vertical",
        yAxis: undefined,
        fontSizeMultiplier: 0.8,
        axisFontSizeMultiplier: undefined,
        activeTab: undefined,
        showToolboxZoom: true,
        showAbbr: false,
        theme: chartTheme,
      });
    }, [lineData, chartTheme, effectiveYAxisConfig]);

    const numericColumnsCount = useMemo(() => {
      return lineData.filter(
        (col) =>
          col.columnName !== "timestamp" &&
          ["double", "float", "int", "int32", "int64"].includes(col.columnType)
      ).length;
    }, [lineData]);

    // **Expose reset method to parent**
    useImperativeHandle(ref, () => ({
      resetYAxisConfig: () => setYAxisConfig(null), // Reset to null to use default config
    }));

    const { token } = theme.useToken();
    console.log({ numericColumns, lineData });

    if (!loading && (!data || data.length === 0)) {
      return (
        <div
          className="flex h-full items-center justify-center rounded-lg bg-white"
          style={{
            border: `1px solid ${token.colorBorder}`,
            backgroundColor: token.colorBgContainer,
          }}
        >
          <span style={{ color: token.colorTextSecondary }}>
            No dispatch data available
          </span>
        </div>
      );
    }

    return (
      <div className="relative h-full w-full" style={{ position: "relative" }}>
        {modalOpen && (
          <YAxisConfiguratorModal
            selectedOptions={effectiveYAxisConfig}
            numericColumns={numericColumns}
            ranges={ranges}
            open={modalOpen}
            columns={lineData}
            chartType="line"
            onCancel={() => setModalOpen(false)}
            onSave={handleSave}
          />
        )}

        <div style={{ height: "100%", width: "100%" }}>
          <Echart
            title="Production"
            chartType="line"
            options={chartOptions}
            loading={fetching || loading}
            columnsLength={numericColumnsCount}
            onOpenYaxisModal={() => setModalOpen(true)}
          />
          {/* <ECompactChart
            title="Production"
            options={chartOptions}
            height="100%"
            width="100%"
            chartType="line"
            onOpenYaxisModal={() => setModalOpen(true)}
            columnsLength={numericColumnsCount}
            fontSizeMultiplier={18 / 14} // 1.286 - to match text-lg (18px) like Total Water Usage
            loading={fetching || loading}
          /> */}
        </div>
      </div>
    );
  }
);

DailyDispatchLineChart.displayName = "DailyDispatchLineChart";

export default DailyDispatchLineChart;
