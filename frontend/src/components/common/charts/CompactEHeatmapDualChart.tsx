// Compact version of EHeatmapDualChart with minimal controls for tight layouts
import React, {
  memo,
  useMemo,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
  useEffect,
} from "react";
import EBaseChart from "./EBaseChart";
import { heatmapDualChartMapper } from "@/utils/chartMappers";
import {
  HeatmapConfig,
  HEATMAP_COLOR_SCHEMES,
  createAbbreviation,
} from "@/utils/chartConfig";
import { getHeatMapConfig } from "@/utils/themeChartConfig";
import { formatColumnName } from "@/utils/helpers";
import HeatmapConfiguratorModal from "../modals/HeatmapConfiguratorModal";
import HeatmapKpiConfigModal, {
  KpiConfig,
} from "../modals/HeatmapKpiConfigModal";
import { ApiColumn } from "./EHeatmapDualChart";
import { getColorForValue as getColorForValueUtil } from "@/utils/colorUtils";
import { Tooltip, theme, message } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import useChartTheme from "@/hooks/useChartTheme";
import {
  useSaveHeatmapWidgetMutation,
  useGetHeatmapWidgetQuery,
} from "@/store/api/heatMapPumpApi";
import Echart from "./Echart";

// Red-to-green color scheme (red for high values, green for low values)
const RED_TO_GREEN_SCHEME = HEATMAP_COLOR_SCHEMES.redToGreen.colors;

type CompactEHeatmapDualChartProps = {
  heatmapData: ApiColumn[];
  showLabels?: boolean;
  xAxisName?: string;
  yAxisName?: string;
  heatmapConfig?: HeatmapConfig;
  title?: string;
  height?: string;
  width?: string | number;
  message?: string;
  displayKpiConfiguration?: boolean;
  loading: boolean;
  onConfigureClick?: () => void;
  showConfigModal?: boolean; // Optional: hide config modals for compact version
  showConfigButton?: boolean; // Optional: show configuration button
  siteId?: string;
  pumpId?: string;
  page?: string;
};

export interface CompactEHeatmapDualChartRef {
  openConfigModal: () => void;
}

const CompactEHeatmapDualChart = forwardRef<
  CompactEHeatmapDualChartRef,
  CompactEHeatmapDualChartProps
>(
  (
    {
      heatmapData,
      showLabels = false,
      xAxisName,
      yAxisName,
      title,
      height = "100%",
      width = "100%",
      displayKpiConfiguration,
      loading,
      showConfigModal = true, // Default to true
      showConfigButton = false, // Default to false for compact behavior
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
    const [userGlobalConfig, setUserGlobalConfig] =
      useState<HeatmapConfig | null>(null);

    const chartTheme = useChartTheme();
    const { token } = theme.useToken();

    // API hooks for widget save/load
    const [saveWidget, { isLoading: isSaving }] =
      useSaveHeatmapWidgetMutation();

    // Log the params being used for the query
    useEffect(() => {
      if (siteId && pumpId && page) {
        console.log("Fetching widget config with:", {
          site_id: siteId,
          pump_id: pumpId,
          page,
        });
      }
    }, [siteId, pumpId, page]);

    const {
      data: savedWidget,
      isLoading: isLoadingWidget,
      error: widgetError,
    } = useGetHeatmapWidgetQuery(
      { site_id: siteId!, pump_id: pumpId!, page: page! },
      { skip: !siteId || !pumpId || !page }
    );

    // Log API response or error
    useEffect(() => {
      if (widgetError) {
        console.error("Error fetching widget config:", widgetError);
      }
      if (savedWidget) {
        console.log("Widget config fetched successfully:", savedWidget);
      }
    }, [savedWidget, widgetError]);

    // Load saved configuration (merging happens in kpiConfigs memo)
    useEffect(() => {
      if (savedWidget?.data?.columns) {
        console.log("Loading saved widget config:", savedWidget.data.columns);

        const savedConfigs: KpiConfig[] = savedWidget.data.columns.map(
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

    // Dynamic icon button style using theme tokens
    const iconButtonStyle: React.CSSProperties = {
      width: "34px",
      height: "32px",
      padding: "9px 10px",
      borderRadius: "6px",
      border: `1px solid ${token.colorBorder}`,
      backgroundColor: token.colorBgContainer,
      boxShadow: "0px 2px 0px 0px rgba(0, 0, 0, 0.016)",
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

    const DEFAULT_SCHEME = RED_TO_GREEN_SCHEME;

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

      // Merge: Start with derived configs, then apply saved user configs
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

      console.log("Final kpiConfigs after merge:", result);
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
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
            <span>Value:</span>
            <span style="font-weight: bold;">${formattedValue}</span>
          </div>
        </div>`;
        }

        const categoryName = params.value?.[0] ?? "";
        const rack = formatColumnName(params.value?.[1] ?? "");
        const value = params.value?.[2] ?? "";

        return `${categoryName} (${rack}): ${value}`;
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
        // Use red-to-green colors by default (red for high, green for low)
        const defaultColors =
          (globalConfig as any)?.customColors || RED_TO_GREEN_SCHEME;
        const customHeatmapConfig: HeatmapConfig = {
          colorScheme,
          startValue: globalConfig?.startValue ?? visualMap?.min ?? 0,
          endValue: globalConfig?.endValue ?? visualMap?.max ?? 100,
          ...(defaultColors ? { customColors: defaultColors } : {}),
        };

        let chartOptions: any;

        if (displayKpiConfiguration) {
          // For KPI configuration, calculate colors per data point based on each KPI's min/max range
          const data: any[] = [];
          (columns[0]?.dataSource || []).forEach((pump, xIdx) => {
            yAxis.data.forEach((attrName: string) => {
              const attr = yAxisIndex.find((a) => a.columnName === attrName);
              const value = attr?.dataSource?.[xIdx];
              const formattedValue =
                typeof value === "number" ? Number(value.toFixed(2)) : value;

              // Find the KPI config for this attribute
              const kpiConfig = kpiConfigs.find((kpi) => kpi.name === attrName);
              const min = kpiConfig?.min ?? attr?.min ?? 0;
              const max = kpiConfig?.max ?? attr?.max ?? 100;
              const colors = kpiConfig?.colors || RED_TO_GREEN_SCHEME;

              // Calculate color using red-to-green gradient
              const color = getColorForValueUtil(value, {
                min,
                max,
                colors,
              });

              // Swap coordinates: [x, y, value] -> [y, x, value] for swapped axis positions
              data.push({
                value: [attrName, pump, formattedValue],
                itemStyle: { color },
              });
            });
          });
          const enhancedSeries = [
            {
              name: "Pump Attributes",
              type: "heatmap" as const,
              data,
              label: showLabels
                ? {
                    show: true,
                    fontSize: 12,
                    color: "#000",
                    fontWeight: 700,
                    formatter: (params: any) => {
                      const dataValue = params.data?.value || params.value;
                      const value = Array.isArray(dataValue)
                        ? dataValue[2]
                        : dataValue;
                      return typeof value === "number" ? value.toFixed(2) : "";
                    },
                  }
                : { show: false },
            },
          ];

          chartOptions = getHeatMapConfig(
            enhancedSeries,
            columns,
            xAxis,
            yAxis,
            { min: 0, max: 0, show: false },
            customHeatmapConfig
          );

          // Remove dataZoom to hide bottom zoom-bar
          delete chartOptions.dataZoom;
          // Keep visualMap but hide it - ECharts requires visualMap for heatmap series
          // Ensure visualMap exists (required by ECharts for heatmap series)
          if (!chartOptions.visualMap) {
            chartOptions.visualMap = {
              min: 0,
              max: 100,
              show: false,
            };
          } else {
            chartOptions.visualMap.show = false;
          }
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

        // Swap axis positions: x-axis on left (vertical), y-axis on top (horizontal)
        // Swap data coordinates from [x, y, value] to [y, x, value]
        const swappedSeries = chartOptions.series?.map((s: any) => {
          if (s.type === "heatmap" && Array.isArray(s.data)) {
            return {
              ...s,
              data: s.data.map((item: any) => {
                if (Array.isArray(item) && item.length >= 3) {
                  // Swap x and y coordinates: [x, y, value] -> [y, x, value]
                  return [item[1], item[0], item[2]];
                }
                return item;
              }),
              label: showLabels
                ? {
                    show: true,
                    fontSize: 12,
                    color: token.colorText,
                    fontWeight: 700,
                    formatter: (params: any) => {
                      const value = params.data?.[2] ?? params.value?.[2];
                      return typeof value === "number" ? value.toFixed(2) : "";
                    },
                  }
                : { show: false },
            };
          }
          return s;
        });

        // Remove any existing dataZoom to hide bottom zoom-bar
        if (chartOptions.dataZoom) {
          delete chartOptions.dataZoom;
        }

        return {
          ...chartOptions,
          series: swappedSeries,
          // Swap axis configurations: x-axis becomes vertical on left, y-axis becomes horizontal on top
          xAxis: {
            ...chartOptions.yAxis,
            position: "left",
            axisLabel: {
              ...((chartOptions.yAxis && chartOptions.yAxis.axisLabel) || {}),
              fontWeight: 400,
              fontFamily: "Figtree",
              fontSize: 12,
              color: token.colorText,
              margin: 4,
              interval: 0,
              formatter: function (value: string) {
                return formatColumnName(value)?.replace(/ /g, "\n");
              },
            },
          },
          yAxis: {
            ...chartOptions.xAxis,
            position: "top",
            show: true,
            axisLine: {
              show: true,
              lineStyle: { color: token.colorBorder },
            },
            axisTick: {
              show: true,
              lineStyle: { color: token.colorBorder },
            },
            axisLabel: {
              ...((chartOptions.xAxis && chartOptions.xAxis.axisLabel) || {}),
              show: true,
              fontWeight: "400",
              fontFamily: "Figtree",
              fontSize: 12,
              color: token.colorText,
              interval: 0,
              formatter: function (value: string) {
                let transformedValue = value;

                if (chartOptions.xAxis.data?.length > 15) {
                  transformedValue = value.replace(/Pump\s+(\d+)/, "P$1");
                }

                return formatColumnName(transformedValue);
              },
            },
          },
          grid: {
            ...chartOptions.grid,
            left: 0,
            top: "3%", // Increased top margin to accommodate top-positioned y-axis
            bottom: "2%",
            right: displayKpiConfiguration ? 12 : 65, // Right margin: 12 when KPI config (no visual map), 65 when visual map shown
            containLabel: true,
          },
          visualMap: displayKpiConfiguration
            ? {
                // When using KPI configuration, keep visualMap but hide it (required by ECharts)
                ...(chartOptions.visualMap || {}),
                show: false,
                min: 0,
                max: 100,
              }
            : {
                // Show visualMap when not using KPI configuration
                ...(chartOptions.visualMap || {}),
                show: true,
                orient: "vertical",
                right: 0,
                top: "5%",
                itemWidth: 15,
                itemHeight: 380,
                textStyle: {
                  color: token.colorText,
                  fontSize: 14,
                },
                textGap: 8,
                precision: 3,
                formatter: (value: any) => {
                  return typeof value === "number" ? value.toFixed(3) : "0.000";
                },
                inRange: {
                  color: defaultColors,
                },
                min: globalConfig?.startValue ?? visualMap?.min ?? 0,
                max: globalConfig?.endValue ?? visualMap?.max ?? 100,
                calculable: true,
              },
          tooltip: {
            position: "top",
            backgroundColor: token.colorBgElevated,
            borderColor: token.colorBorder,
            borderRadius: 4,
            padding: [8, 10],
            textStyle: {
              color: token.colorText,
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
        {
          colorScheme: "redToGreen",
          startValue: 0,
          endValue: 0,
          customColors: RED_TO_GREEN_SCHEME,
        }
      );

      return {
        ...emptyOptions,
        grid: {
          ...emptyOptions.grid,
          top: "3%",
          left: 12,
          right: 50,
          bottom: "2%",
        },
        xAxis: { ...emptyOptions.xAxis, position: "left" },
        yAxis: { ...emptyOptions.yAxis, position: "top" },
        graphic: emptyChartGraphic,
      };
    }, [
      heatmapData,
      xAxisName,
      yAxisName,
      showLabels,
      globalConfig,
      tooltipFormatter,
      displayKpiConfiguration,
      kpiConfigs,
      emptyChartGraphic,
      chartTheme,
      token.colorBgElevated,
      token.colorBorder,
      token.colorText,
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
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          overflow: "hidden",
        }}
      >
        {/* <EBaseChart
          AdditionalActions={
            showConfigButton ? (
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
                >
                  <SettingOutlined width="14" height="14" />
                </button>
              </Tooltip>
            ) : undefined
          }
          chartType="heatmap"
          options={options}
          height={height}
          width={width}
          title={title}
          showZoomControls={false}
          showMenu={false}
          showToolboxZoom={false}
          showRestore={false}
          loading={isLoading}
        /> */}

        <Echart
          height={height}
          moreActions={
            showConfigButton ? (
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
                >
                  <SettingOutlined width="14" height="14" />
                </button>
              </Tooltip>
            ) : undefined
          }
          chartType="heatmap"
          options={options}
          title={title}
          showZoomControls={false}
          showMenu={false}
          showRestore={false}
          showYAxisConfig={false}
          loading={isLoading}
        />

        {showConfigModal && (
          <>
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
          </>
        )}
      </div>
    );
  }
);

CompactEHeatmapDualChart.displayName = "CompactEHeatmapDualChart";

export default memo(CompactEHeatmapDualChart);
