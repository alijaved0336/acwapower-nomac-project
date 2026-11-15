import type { EChartsYAxisConfig } from "@/utils/chartConfig";

export const alertsChartConfig: Record<
  string,
  {
    title: string;
    yAxisConfig: EChartsYAxisConfig[];
  }
> = {
  Conductivity: {
    title: "Conductivity",
    yAxisConfig: [
      {
        seriesName: "ActualValue",
        show: true,
        opposite: false,
        axisLabel: { formatter: (val: number) => val.toFixed(2) },
        title: { text: "Actual / Expected / Residual" },
        axisBorder: { show: true, color: "#888" },
        axisTicks: { show: true, color: "#888", width: 1 },
        tooltip: { enabled: true },
      },
    ],
  },
  Pressure: {
    title: "Pressure",
    yAxisConfig: [
      {
        seriesName: "ActualValue",
        show: true,
        opposite: false,
        axisLabel: { formatter: (val: number) => val.toFixed(2) },
        title: { text: "Pressure Value" },
        axisBorder: { show: true, color: "#888" },
        axisTicks: { show: true, color: "#888", width: 1 },
        tooltip: { enabled: true },
      },
    ],
  },
  Flow: {
    title: "Flow",
    yAxisConfig: [
      {
        seriesName: "ActualValue",
        show: true,
        opposite: false,
        axisLabel: { formatter: (val: number) => val.toFixed(2) },
        title: { text: "Flow Value" },
        axisBorder: { show: true, color: "#888" },
        axisTicks: { show: true, color: "#888", width: 1 },
        tooltip: { enabled: true },
      },
    ],
  },
  ResidualChart: {
    title: "Residual Chart",
    yAxisConfig: [
      {
        seriesName: "ResidualValue",
        show: true,
        opposite: false,
        axisLabel: { formatter: (val: number) => val.toFixed(2) },
        title: { text: "Residual Value" },
        axisBorder: { show: true, color: "#888" },
        axisTicks: { show: true, color: "#888", width: 1 },
        tooltip: { enabled: true },
      },
    ],
  },
};
