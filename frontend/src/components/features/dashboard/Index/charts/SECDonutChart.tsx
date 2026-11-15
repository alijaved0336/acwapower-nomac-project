// components/SECDonutChart.tsx
import ReactECharts from "echarts-for-react";
import { useMemo, useState, useEffect, useRef } from "react";
import { useAppSelector } from "../../../../../hooks";
import { Card, theme } from "antd";
import { PlantKPI } from "@/types/energy.types";
import ChartSpinner from "../../../../common/ChartSpinner";

interface SECDonutChartProps {
  data: PlantKPI[];
  title?: string;
  selectedPlant?: string;
  loading: boolean;
}

function SECDonutChart({
  data,
  title = "SEC",
  selectedPlant = "All Plants",
  loading,
}: Readonly<SECDonutChartProps>) {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  const chartRef = useRef<ReactECharts>(null);

  // Get all plant data (not filtered)
  const allPlantsData = useMemo(() => {
    const secRow = data?.find((item) => item.kpi === "Sec");
    if (!secRow) return [];

    return [
      {
        id: "Jubail-Jazlah",
        name: "Jubail 3A IWP",
        value: parseFloat(secRow["Jubail Energy Plant"]) || 0,
        plantType: "Jubail Energy Plant",
      },
      {
        id: "UAQ",
        name: "Umm Al Quwain",
        value: parseFloat(secRow["UAQ Energy Plant"]) || 0,
        plantType: "UAQ Energy Plant",
      },
      {
        id: "Rabigh3",
        name: "Rabigh 3",
        value: parseFloat(secRow["Rabigh Energy Plant"]) || 0,
        plantType: "Rabigh Energy Plant",
      },
      {
        id: "STPC",
        name: "Shuaibah",
        value: parseFloat(secRow["STPC Energy Plant"]) || 0,
        plantType: "STPC Energy Plant",
      },
    ].filter((item) => item.value > 0);
  }, [data]);

  // Build legend selected state based on dropdown
  const legendSelected = useMemo(() => {
    if (selectedPlant === "All Plants") {
      return allPlantsData.reduce(
        (acc, item) => {
          acc[item.name] = true;
          return acc;
        },
        {} as Record<string, boolean>
      );
    }

    return allPlantsData.reduce(
      (acc, item) => {
        acc[item.name] = item.plantType === selectedPlant;
        return acc;
      },
      {} as Record<string, boolean>
    );
  }, [allPlantsData, selectedPlant]);

  // Track active legends
  const [activeLegends, setActiveLegends] =
    useState<Record<string, boolean>>(legendSelected);

  // Sync activeLegends when dropdown changes
  useEffect(() => {
    setActiveLegends(legendSelected);
  }, [legendSelected]);

  // Calculate total based on active legends
  const total = useMemo(() => {
    return allPlantsData
      .filter((item) => activeLegends[item.name])
      .reduce((sum, item) => sum + item.value, 0);
  }, [allPlantsData, activeLegends]);

  // Colors for each plant
  const colors = useMemo(
    () => ["#357E7A", "#56B8B3", "#90D0CD", "#BEE4E2"],
    []
  );

  // Handle legend selection change
  const onEvents = useMemo(
    () => ({
      legendselectchanged: (params: any) => {
        setActiveLegends(params.selected);
      },
    }),
    []
  );

  // Handle chart ready - resize after render
  const handleChartReady = (chartInstance: any) => {
    // Resize immediately
    setTimeout(() => {
      chartInstance?.resize();
    }, 0);

    // Resize again after a short delay to ensure everything is loaded
    setTimeout(() => {
      chartInstance?.resize();
    }, 100);
  };

  const option = useMemo(
    () => ({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        formatter: "{b}: {c} kWh/m3 ({d}%)",
        backgroundColor: token.colorBgElevated,
        borderColor: token.colorBorder,
        textStyle: {
          color: token.colorText,
        },
      },

      legend: {
        show: !loading,
        orient: "vertical",
        right: "5%",
        top: "center",
        itemGap: 16,
        itemWidth: 12,
        itemHeight: 12,
        icon: "roundRect",
        backgroundColor: token.colorBgContainer,
        borderColor: token.colorBorder,
        borderWidth: 1,
        borderRadius: 8,
        padding: [15, 20],
        selected: legendSelected,

        textStyle: {
          color: token.colorText,
          fontSize: 13,
          rich: {
            name: {
              width: 120,
              fontSize: 13,
              color: token.colorText,
            },
            value: {
              width: 50,
              align: "right",
              fontSize: 13,
              fontWeight: "bold",
              color: token.colorText,
            },
            unit: {
              fontSize: 11,
              color: token.colorTextSecondary,
            },
          },
        },
        formatter: (name: string) => {
          const item = allPlantsData.find((d) => d.name === name);
          const value = item?.value.toFixed(2) || "0.00";
          return `{name|${name}}{value|${value}} {unit|kWh/m3}`;
        },
      },
      series: [
        {
          type: "pie",
          radius: ["60%", "80%"],
          center: ["20%", "50%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderColor: token.colorBgContainer,
            borderWidth: 1,
          },
          label: {
            show: true,
            position: "center",
            // formatter: function () {
            //   return `{value|${total.toFixed(2)}}\n{unit|kWh/m³}\n{label|Total}`;
            // },
            formatter: `{value|0.00}\n{unit|kWh/m³}\n{label|Total}`,
            rich: {
              value: {
                fontSize: 24,
                fontWeight: "bold",
                color: isDark ? "#ffffff" : "#111827",
                lineHeight: 32,
                align: "center",
              },
              unit: {
                fontSize: 12,
                color: isDark ? "#9ca3af" : "#6b7280",
                lineHeight: 20,
                align: "center",
              },
              label: {
                fontSize: 11,
                color: isDark ? "#9ca3af" : "#6b7280",
                lineHeight: 18,
                align: "center",
              },
            },
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 26,
              fontWeight: "bold",
            },
          },
          labelLine: {
            show: false,
          },
          data: allPlantsData.map((item, index) => ({
            value: item.value,
            name: item.name,
            itemStyle: {
              color: colors[index % colors.length],
            },
          })),
        },
      ],
    }),
    [allPlantsData, isDark, colors, legendSelected, loading]
  );

  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    if (chartInstance) {
      chartInstance.setOption({
        series: [
          {
            label: {
              formatter: `{value|${total.toFixed(2)}}\n{unit|kWh/m³}\n{label|Total}`,
            },
          },
        ],
      });
    }
  }, [total, allPlantsData, isDark, colors, legendSelected, loading]);

  return (
    <div className="relative flex h-full flex-col pb-8">
      {loading && <ChartSpinner />}
      <h3 className="mb-4 text-lg font-semibold text-gray-900 transition-colors dark:text-white">
        {title}
      </h3>
      <div className="relative" style={{ height: "100%" }}>
        <ReactECharts
          ref={chartRef}
          option={option}
          style={{ height: "100%", width: "100%" }}
          opts={{ renderer: "svg" }}
          notMerge={false}
          lazyUpdate={true}
          onEvents={onEvents}
          onChartReady={handleChartReady} // Resize after chart is ready
        />

        {/* Centered text overlay */}
        {/* <div
          className="pointer-events-none absolute inset-0 flex items-center"
          style={{ width: "40%" }}
        >
          <div
            className="flex flex-col items-center justify-center"
            style={{ width: "100%" }}
          >
            <p className="text-3xl font-bold text-gray-900 transition-colors dark:text-white">
              {total.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500 transition-colors dark:text-gray-400">
              kWh/m3
            </p>
            <p className="text-sm text-gray-500 transition-colors dark:text-gray-400">
              Total
            </p>
          </div>
        </div> */}
      </div>
    </div>
  );
}

export default SECDonutChart;
