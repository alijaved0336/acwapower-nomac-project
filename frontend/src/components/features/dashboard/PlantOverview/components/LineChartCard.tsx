import React, {
  forwardRef,
  useMemo,
  useImperativeHandle,
  useEffect,
} from "react";
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import { usePlantOverviewContext } from "../context/plantOverviewContext";
import { mapApiGraphToChartColumns } from "../utils/plantOverviewHelper";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";
import { useState, useTransition } from "react";
import Spinner from "@/components/common/Spinner"; // same as demo me use hua tha
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import ECompactChart from "../../../../common/charts/ECompactChart";
import { useAppSelector } from "@/hooks";
import useChartTheme from "../../../../../hooks/useChartTheme";
import Echart from "../../../../common/charts/Echart";

interface PlantOverviewChartProps {
  compact?: boolean;
}

export interface LineChartCardRef {
  resetYAxisConfig: () => void;
}

const LineChartCard = forwardRef<LineChartCardRef, PlantOverviewChartProps>(
  ({ compact = false }, ref) => {
    const { graph, loading, modified, from_date, to_date } =
      usePlantOverviewContext();
    const theme = useChartTheme();
    const isDark = useAppSelector((state) => state.settings.mode) === "dark";

    const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

    const [yaxisOptions, setYaxisOptions] = useState<
      EChartsYAxisConfig[] | null
    >(null);
    const [, startTransition] = useTransition();

    const { columns, yAxisConfig } = useMemo(
      () => mapApiGraphToChartColumns(graph),
      [graph]
    );

    // Default Y-axis configuration for Plant Overview: Production and Dispatched flow on left, Plant SEC on right
    const defaultYAxisConfig = useMemo<EChartsYAxisConfig[]>(() => {
      if (!columns || columns.length === 0) return [];

      const configs: EChartsYAxisConfig[] = [];

      // Find Production column
      const productionColumn = columns.find(
        (col) => col.columnName === "Production (m³/h)"
      );
      if (productionColumn) {
        configs.push({
          seriesName: productionColumn.columnName,
          show: true,
          opposite: false, // Left axis
          title: { text: productionColumn.columnName },
        });
      }

      // Find Dispatched flow column
      const dispatchedColumn = columns.find(
        (col) => col.columnName === "Dispatched flow (m³/h)"
      );
      if (dispatchedColumn) {
        configs.push({
          seriesName: dispatchedColumn.columnName,
          show: true,
          opposite: false, // Left axis
          title: { text: dispatchedColumn.columnName },
        });
      }

      // Find Plant SEC column
      const plantSecColumn = columns.find(
        (col) => col.columnName === "Plant SEC (kW/m³)"
      );
      if (plantSecColumn) {
        configs.push({
          seriesName: plantSecColumn.columnName,
          show: true,
          opposite: true, // Right axis
          title: { text: plantSecColumn.columnName },
        });
      }

      return configs;
    }, [columns]);

    // Set default configuration when columns are available and no manual config exists
    useEffect(() => {
      if (defaultYAxisConfig.length > 0 && yaxisOptions === null) {
        setYaxisOptions(defaultYAxisConfig);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [defaultYAxisConfig]);

    // Use default config if no manual config is set, otherwise use manual config
    const effectiveYAxisOptions = useMemo(() => {
      if (yaxisOptions === null) {
        return defaultYAxisConfig;
      }
      return yaxisOptions;
    }, [yaxisOptions, defaultYAxisConfig]);

    // Chart configuration logic (previously in ELineChart)
    const options = useMemo(() => {
      const { series, xAxis } = mapXYSeries("line", columns);
      const opts = getLineBarScatterChartConfig({
        series,
        columns,
        xAxis,
        yaxisOptions: effectiveYAxisOptions,
        fontSizeMultiplier: 0.8,
        axisFontSizeMultiplier: undefined,
        activeTab: undefined,
        showToolboxZoom: true,
        showAbbr: false,
        theme: theme,
      });

      return opts;
    }, [columns, effectiveYAxisOptions, theme]);

    const showSpinner = loading;

    const { numericColumns, ranges } = useYAxisConfigurator(columns || []);

    const apiConfigs = useMemo(
      () => [
        {
          key: "plant_overview_chart",
          name: "Plant Overview Line Chart",
          data_availability_for_given_date: modified === true ? false : true,
          from_date: from_date,
          to_date: to_date,
          isLoading: loading,
          isFetching: loading,
        },
      ],
      [modified, from_date, to_date, loading]
    );

    useApiNotifications({
      apis: apiConfigs,
    });
    // Handle modal save
    const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
      startTransition(() => {
        if (Array.isArray(config)) {
          setYaxisOptions(config);
        }
      });
      setIsConfigModalOpen(false);
    };

    // **Expose reset method to parent**
    useImperativeHandle(ref, () => ({
      resetYAxisConfig: () => setYaxisOptions(null), // Reset to null to use default config
    }));

    return (
      <div className="h-full w-full !min-w-0">
        {isConfigModalOpen && (
          <YAxisConfiguratorModal
            selectedOptions={effectiveYAxisOptions}
            numericColumns={numericColumns}
            ranges={ranges}
            open={isConfigModalOpen}
            columns={columns || []}
            chartType="line"
            onCancel={() => setIsConfigModalOpen(false)}
            onSave={handleSave}
          />
        )}

        <Echart
          title="Production and Dispatched flow"
          chartType="line"
          options={options}
          loading={showSpinner}
          onOpenYaxisModal={() => setIsConfigModalOpen(true)}
          columnsLength={numericColumns?.length ?? 0}
        />
      </div>
    );
  }
);

LineChartCard.displayName = "LineChartCard";

export default LineChartCard;
