import React, {
  FC,
  memo,
  useMemo,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
  useEffect,
} from "react";
import Echart from "./Echart";
import { heatmapDualChartMapper } from "@/utils/chartMappers";
import {
  getHeatMapConfig,
  HeatmapConfig,
  HEATMAP_COLOR_SCHEMES,
} from "@/utils/themeChartConfig";
import { getColorForValue as getColorForGradient } from "@/utils/colorUtils";
import HeatmapConfiguratorModal from "../modals/HeatmapConfiguratorModal";
import HeatmapKpiConfigModal, {
  KpiConfig,
} from "../modals/HeatmapKpiConfigModal";
import { theme, Tooltip, message } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { ATTRIBUTE_UNITS } from "../../features/PumpAnalysis/utils/chartHelpers";
import useChartTheme from "../../../hooks/useChartTheme";
import {
  useSaveHeatmapWidgetMutation,
  useGetHeatmapWidgetQuery,
} from "@/store/api/heatMapPumpApi";

export interface ApiColumn {
  columnType: string;
  columnName: string;
  dataSource: any[];
  [key: string]: any;
}

type EHeatmapDualChartProps = {
  heatmapData: ApiColumn[];
  showLabels?: boolean;
  xAxisName?: string;
  yAxisName?: string;
  heatmapConfig?: HeatmapConfig;
  title?: string;
  height?: number;
  width?: number;
  message?: string;
  displayKpiConfiguration?: boolean;
  loading: boolean;
  onConfigureClick?: () => void;
  siteId?: string;
  pumpId?: string;
  page?: string;
};

export interface EHeatmapDualChartRef {
  openConfigModal: () => void;
}

const EHeatmapDualChart = forwardRef<
  EHeatmapDualChartRef,
  EHeatmapDualChartProps
>(
  (
    {
      heatmapData,
      showLabels = false,
      xAxisName,
      yAxisName,
      title,
      height,

      displayKpiConfiguration,
      loading,
      onConfigureClick,
      siteId,
      pumpId,
      page,
    },
    ref
  ) => {
    const [kpiConfigModalOpen, setKpiConfigModalOpen] = useState(false);
    const [globalConfigModalOpen, setGlobalConfigModalOpen] = useState(false);
    const [userKpiConfigs, setUserKpiConfigs] = useState<KpiConfig[] | null>(
      null
    );

    const { token } = theme.useToken();
    const chartTheme = useChartTheme();

    const [userGlobalConfig, setUserGlobalConfig] =
      useState<HeatmapConfig | null>(null);

    // API hooks for widget save/load
    const [saveWidget, { isLoading: isSaving }] =
      useSaveHeatmapWidgetMutation();

    const {
      data: savedWidget,
      isLoading: isLoadingWidget,
      error: widgetError,
    } = useGetHeatmapWidgetQuery(
      { site_id: siteId!, pump_id: pumpId!, page: page! },
      { skip: !siteId || !pumpId || !page }
    );

    // Load saved configuration (merging happens in kpiConfigs memo)
    useEffect(() => {
      if (savedWidget) {
        const savedConfigs: KpiConfig[] = savedWidget?.data?.columns?.map(
          (col) => ({
            name: col.columnName,
            unit: "", // Will be filled from derived configs during merge
            min: col.yAxisOptions.min,
            max: col.yAxisOptions.max,
            colors: col.yAxisOptions.colors,
            colorScheme: col.yAxisOptions.colorScheme,
          })
        );

        setUserKpiConfigs(savedConfigs);
      }
    }, [savedWidget]);

    const iconButtonStyle: React.CSSProperties = {
      width: "34px",
      height: "32px",
      padding: "9px 10px",
      borderRadius: "6px",
      border: `1px solid ${token.colorBorder}`,
      backgroundColor: token.colorBgContainer,
      boxShadow: `0px 2px 0px 0px ${token.colorFillQuaternary}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      cursor: "pointer",
      transition: "all 0.2s",
      opacity: 1,
    };

    // Expose modal opening function via ref
    useImperativeHandle(ref, () => ({
      openConfigModal: () => {
        if (displayKpiConfiguration) {
          setKpiConfigModalOpen(true);
        } else {
          setGlobalConfigModalOpen(true);
        }
      },
    }));

    // Default color scheme
    const DEFAULT_SCHEME = HEATMAP_COLOR_SCHEMES.redToGreen.colors;

    // --- DERIVED KPI CONFIGS ---
    const derivedKpiConfigs = useMemo(() => {
      if (!heatmapData?.length) return [];
      const { yAxisIndex = [] } = heatmapDualChartMapper(heatmapData, {
        xAxisName,
        yAxisName,
        showLabels,
      });
      return yAxisIndex.map((yAxisIndex) => {
        let min = yAxisIndex.min;
        let max = yAxisIndex.max;
        if (min == null) min = 0;
        if (max == null) max = 100;
        return {
          name: yAxisIndex.columnName || "Unknown",
          unit: "",
          min,
          max,
          colors: DEFAULT_SCHEME,
        };
      });
    }, [heatmapData, xAxisName, yAxisName, showLabels, DEFAULT_SCHEME]);

    const kpiConfigs = useMemo(() => {
      if (!displayKpiConfiguration) return [];
      if (!userKpiConfigs || userKpiConfigs.length === 0)
        return derivedKpiConfigs;

      const result = derivedKpiConfigs.map((derived) => {
        const userConfig = userKpiConfigs.find(
          (uc) => uc.name === derived.name
        );
        if (userConfig) {
          return {
            ...derived, // Keep unit and other derived fields
            min: userConfig.min,
            max: userConfig.max,
            colors: userConfig.colors,
            colorScheme: userConfig.colorScheme,
          };
        }
        return derived;
      });
      return result;
    }, [displayKpiConfiguration, userKpiConfigs, derivedKpiConfigs]);

    // --- DERIVED GLOBAL CONFIG ---
    const derivedGlobalConfig = useMemo(() => {
      if (!heatmapData?.length) {
        return { colorScheme: "redToGreen", startValue: 0, endValue: 100 };
      }
      const { visualMap } = heatmapDualChartMapper(heatmapData, {
        xAxisName,
        yAxisName,
        showLabels,
      });
      return {
        colorScheme: "redToGreen",
        startValue: visualMap?.min ?? 0,
        endValue: visualMap?.max ?? 100,
      };
    }, [heatmapData, xAxisName, yAxisName, showLabels]);

    const globalConfig = !displayKpiConfiguration
      ? userGlobalConfig || derivedGlobalConfig
      : derivedGlobalConfig;

    // --- COLOR CALCULATION ---
    const getColorForValue = useCallback(
      (value: number, yAxisIndex: number) => {
        const kpi = kpiConfigs[yAxisIndex];
        if (!kpi) return "#cccccc";

        const colors = kpi.colors?.length ? kpi.colors : DEFAULT_SCHEME;

        return getColorForGradient(
          value,
          {
            min: kpi.min,
            max: kpi.max,
            colors,
          },
          "#cccccc"
        );
      },
      [kpiConfigs, DEFAULT_SCHEME]
    );

    // --- TOOLTIP ---
    const tooltipFormatter = useMemo(
      () => (params: any) => {
        const data = params.data || [];
        if (data.length >= 3) {
          const pumpName = data[0];
          const attributeName = data[1];
          const originalValue = data[2];
          const formattedValue = Number(originalValue).toFixed(2);
          return `
        <div style="padding: 5px;">
          <div style="border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 6px; margin-bottom: 6px;">
            <span style="font-size: 0.813rem; font-weight: bold;">${pumpName}</span>
          </div>
          <div style="margin-bottom: 8px; font-size: 0.75rem;">${attributeName}</div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>Value:</span>
            <span style="font-weight: bold;">${formattedValue}</span>
          </div>
        </div>`;
        }
        return `${params.value[0]}-${params.value[1]}:${params.value[2]}`;
      },
      []
    );
    // --- EMPTY CHART MESSAGE ---
    const emptyChartGraphic = useMemo(
      () => [
        {
          type: "group",
          left: "center",
          top: "middle",
          children: [
            {
              type: "text",
              style: {
                text: "No Data Available",
                fontSize: 14,
                fill: "#999",
                lineHeight: 24,
              },
            },
          ],
        },
      ],
      []
    );

    // --- CHART OPTIONS ---
    const options = useMemo(() => {
      if (heatmapData?.length) {
        const { xAxis, yAxis, series, visualMap, columns, yAxisIndex } =
          heatmapDualChartMapper(heatmapData, {
            xAxisName,
            yAxisName,
            showLabels,
          });

        const colorScheme = globalConfig?.colorScheme || "redToGreen";
        // Only add customColors if it exists on globalConfig
        const customHeatmapConfig: HeatmapConfig = {
          colorScheme,
          startValue: globalConfig?.startValue ?? visualMap?.min ?? 0,
          endValue: globalConfig?.endValue ?? visualMap?.max ?? 100,
          ...(globalConfig &&
          "customColors" in globalConfig &&
          globalConfig.customColors
            ? { customColors: (globalConfig as any).customColors }
            : {}),
        };

        let chartOptions: any;

        if (displayKpiConfiguration) {
          // Individual KPI-based coloring
          // Build a single heatmap series with all cells, coloring each cell by its attribute's min/max/colors
          const data: any[] = [];
          (columns[0]?.dataSource || []).forEach((pump, xIdx) => {
            yAxis.data.forEach((attrName: string) => {
              const attr = yAxisIndex.find((a) => a.columnName === attrName);
              const value = attr?.dataSource?.[xIdx];
              const formattedValue =
                typeof value === "number" ? Number(value.toFixed(2)) : value;

              // Find the correct KPI config by NAME, not by y-axis position!
              const kpiIdx = kpiConfigs.findIndex(
                (kpi) => kpi.name === attrName
              );

              const color = getColorForValue(value, kpiIdx);

              data.push({
                value: [pump, attrName, formattedValue],
                itemStyle: { color },
              });
            });
          });
          const enhancedSeries = [
            {
              name: "Pump Attributes",
              type: "heatmap" as const,
              data,
            },
          ];

          chartOptions = getHeatMapConfig(
            enhancedSeries,
            columns,
            xAxis,
            yAxis,
            { min: 0, max: 0, show: false },
            customHeatmapConfig,
            chartTheme
          );

          chartOptions.dataZoom = [
            {
              type: "inside",
              startValue: 0,
              endValue: 100,
              zoomOnMouseWheel: false,
              moveOnMouseMove: false,
              moveOnMouseWheel: false,
              preventDefaultMouseMove: false,
              filterMode: "filter",
            },
            {
              type: "slider",
              startValue: 0,
              endValue: 100,
              show: false,
              filterMode: "filter",
              height: 20,
              bottom: 10,
            },
          ];

          delete chartOptions.visualMap; // Disable global color scale
        } else {
          chartOptions = getHeatMapConfig(
            series,
            columns,
            xAxis,
            yAxis,
            visualMap,
            customHeatmapConfig,
            chartTheme
          );
        }

        return {
          ...chartOptions,

          xAxis: {
            ...chartOptions.xAxis,
            position: "top",
            axisLabel: {
              ...((chartOptions.xAxis && chartOptions.xAxis.axisLabel) || {}),
              fontWeight: 500,
              fontFamily: "Figtree",
              fontSize: 14,
              color: token.colorText,
              interval: 0,
              formatter: function (value: string) {
                if (chartOptions.xAxis.data?.length > 15)
                  return value.replace(/Pump\s+(\d+)/, "P $1");
                return value;
              },
            },
          },
          yAxis: {
            ...chartOptions.yAxis,
            axisLabel: {
              ...((chartOptions.yAxis && chartOptions.yAxis.axisLabel) || {}),
              fontWeight: 500,
              fontFamily: "Figtree",
              fontSize: 14,
              color: token.colorText,
              margin: 4,
              formatter: function (value: string) {
                const unit = ATTRIBUTE_UNITS[value];
                if (unit) {
                  return `{main|${value}} {unit|(${unit})}`;
                }
                return `{main|${value}}`;
              },
              rich: {
                unit: {
                  color: token.colorTextTertiary,
                  fontWeight: 400,
                  fontSize: 12,
                },
              },
            },
          },
          grid: {
            ...chartOptions.grid,
            left: "2%",
            // top: 40,
            bottom: 50,
            right: displayKpiConfiguration ? "2%" : "10%",
            containLabel: true,
          },
          visualMap: displayKpiConfiguration
            ? { show: false }
            : {
                ...chartOptions.visualMap,
                itemHeight: height ? height / 2 : 200,
                itemWidth: 20,
                right: "2%",
                top: "center",
                orient: "vertical",
                calculable: true,
                textStyle: {
                  fontFamily: "Figtree, sans-serif",
                  fontSize: 12,
                  fontWeight: 600,
                  color: token.colorTextSecondary,
                },
              },
          tooltip: {
            position: "top",
            backgroundColor: "rgba(0,0,0,0.85)",
            borderColor: "transparent",
            borderRadius: 4,
            padding: [10, 12],
            textStyle: {
              color: "#fff",
              fontSize: 12,
              fontFamily: "Figtree, sans-serif",
              fontWeight: 600,
            },
            extraCssText: "box-shadow: 0 3px 10px rgba(0,0,0,0.2);",
            formatter: tooltipFormatter,
          },
        };
      }

      const emptyOptions = getHeatMapConfig(
        [],
        [],
        { type: "category", data: [] },
        { type: "category", data: [] },
        { min: 0, max: 0, calculable: true },
        { colorScheme: "redToGreen", startValue: 0, endValue: 0 },
        chartTheme
      );

      return {
        ...emptyOptions,

        grid: { ...emptyOptions.grid, top: "5%" },
        xAxis: { ...emptyOptions.xAxis, position: "top" },
        graphic: emptyChartGraphic,
      };
    }, [
      heatmapData,
      xAxisName,
      yAxisName,
      showLabels,
      globalConfig,
      tooltipFormatter,
      height,
      getColorForValue,
      displayKpiConfiguration,
      kpiConfigs,
      emptyChartGraphic,
      token.colorTextSecondary,
      token.colorTextTertiary,
      chartTheme,
    ]);

    // --- HANDLERS ---
    const handleGlobalConfigChange = useCallback((newConfig: HeatmapConfig) => {
      setUserGlobalConfig({
        colorScheme: newConfig.colorScheme || "redToGreen",
        startValue: newConfig.startValue ?? 0,
        endValue: newConfig.endValue ?? 100,
        customColors: newConfig.customColors,
      });
      setGlobalConfigModalOpen(false);
    }, []);

    const handleKpiConfigChange = useCallback(
      async (newKpiConfigs: KpiConfig[]) => {
        const updated = newKpiConfigs.map((kpi) => ({
          ...kpi,
          colors:
            Array.isArray(kpi.colors) && kpi.colors.length > 1
              ? kpi.colors
              : DEFAULT_SCHEME,
        }));
        setUserKpiConfigs(updated);
        setKpiConfigModalOpen(false);

        // Save to backend if props available
        if (siteId && pumpId && page) {
          try {
            await saveWidget({
              site_id: siteId,
              pump_id: pumpId,
              page,
              columns: updated.map((kpi) => ({
                columnName: kpi.name,
                yAxisOptions: {
                  min: kpi.min,
                  max: kpi.max,
                  colors: kpi.colors,
                  reverse: false,
                  colorScheme: kpi.colorScheme || "redToGreen",
                },
              })),
            }).unwrap();
            message.success("Configuration saved successfully");
          } catch (error) {
            message.error("Failed to save configuration");
            console.error("Save widget error:", error);
          }
        }
      },
      [DEFAULT_SCHEME, siteId, pumpId, page, saveWidget]
    );

    // Combine data loading and widget config loading states
    const isLoading = loading || isLoadingWidget || isSaving;

    return (
      <div style={{ position: "relative", width: "100%", overflow: "hidden" }}>
        <Echart
          moreActions={
            <Tooltip title="Configure Heatmap" placement="top">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (displayKpiConfiguration) {
                    setKpiConfigModalOpen(true);
                  } else {
                    setGlobalConfigModalOpen(true);
                  }
                }}
                style={iconButtonStyle}
                className="hover:bg-gray-50"
              >
                <SettingOutlined width="14" height="14" />
              </button>
            </Tooltip>
          }
          chartType="heatmap"
          options={options}
          height={height ? `${height}px` : "100%"}
          title={title}
          showZoomControls={false}
          showMenu={false}
          loading={isLoading}
          showRestore={false}
          showYAxisConfig={false}
        />

        {displayKpiConfiguration ? (
          <HeatmapKpiConfigModal
            open={kpiConfigModalOpen}
            onCancel={() => setKpiConfigModalOpen(false)}
            onSave={handleKpiConfigChange}
            currentConfigs={kpiConfigs}
            title={title}
          />
        ) : (
          <HeatmapConfiguratorModal
            open={globalConfigModalOpen}
            onCancel={() => setGlobalConfigModalOpen(false)}
            onSave={handleGlobalConfigChange}
            currentConfig={globalConfig}
            valueRange={
              options && options.visualMap
                ? {
                    min: options.visualMap.min,
                    max: options.visualMap.max,
                  }
                : heatmapData &&
                    heatmapData.length > 2 &&
                    heatmapData[2].dataSource &&
                    heatmapData[2].dataSource.length > 0
                  ? {
                      min: Math.min(
                        ...heatmapData[2].dataSource.filter(
                          (v) => typeof v === "number"
                        )
                      ),
                      max: Math.max(
                        ...heatmapData[2].dataSource.filter(
                          (v) => typeof v === "number"
                        )
                      ),
                    }
                  : { min: 0, max: 100 }
            }
          />
        )}
      </div>
    );
  }
);

EHeatmapDualChart.displayName = "EHeatmapDualChart";

export default memo(EHeatmapDualChart);
