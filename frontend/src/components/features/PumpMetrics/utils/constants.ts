import { EChartsYAxisConfig } from "../../../../utils/chartConfig";
import { formatColumnTitle } from "../../../../utils/tableConfig";

export const CHART_CONFIGS = [
  {
    title: "Shaft Power vs Expected",
    defaultX: "Flow",
    defaultY: "Pump_Power",
  },
  {
    title: "Efficiency Actual vs Expected",
    defaultX: "Flow",
    defaultY: "Efficiency",
  },
  {
    title: "Head Actual vs Expected",
    defaultX: "Flow",
    defaultY: "Head",
  },
  {
    title: "SEC Actual vs Expected",
    defaultX: "Flow",
    defaultY: "SEC",
  },
] as const;

export const PUMP_METRICS_COLUMNS = [
  "Pump_Flow",
  "Pump_Power",
  "Pump_Discharge_Press",
  "Pump_Differential_Pressure",
] as const;

export const defaultYAxisConfigPumpChart: EChartsYAxisConfig[] = [
  {
    seriesName: formatColumnTitle("Pump_Flow"),
    show: true,
    title: { text: "Flow (m³/h)" },
    opposite: false,
    min: 0,
    max: 2500,
    axisBorder: { show: true, color: "#333" },
    axisTicks: { show: true, color: "#333", width: 1 },
    tooltip: { enabled: true },
    decimalsInFloat: 2,
  },
  {
    seriesName: formatColumnTitle("Pump_Power"),
    show: true,
    title: { text: "Power Consumption (kW)" },
    opposite: false,
    min: 0,
    max: 300,
    axisBorder: { show: true, color: "#333" },
    axisTicks: { show: true, color: "#333", width: 1 },
    tooltip: { enabled: true },
    decimalsInFloat: 2,
  },
  {
    seriesName: formatColumnTitle("Pump_Discharge_Press"),
    show: true,
    title: { text: "Discharge Pressure (bar)" },
    opposite: true,
    min: 0,
    max: 10,
    axisBorder: { show: true, color: "#333" },
    axisTicks: { show: true, color: "#333", width: 1 },
    tooltip: { enabled: true },
    decimalsInFloat: 2,
  },
  {
    seriesName: formatColumnTitle("Pump_Differential_Pressure"),
    show: true,
    title: { text: "Differential Pressure (bar)" },
    opposite: true,
    min: 0,
    max: 5,
    axisBorder: { show: true, color: "#333" },
    axisTicks: { show: true, color: "#333", width: 1 },
    tooltip: { enabled: true },
    decimalsInFloat: 2,
  },
];
