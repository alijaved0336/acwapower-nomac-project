export const TREND_TABS = [
  { key: "operational", label: "Operational Trend" },
  { key: "performance", label: "Performance Trend" },
] as const;

export const PUMP_CATEGORY_LABELS: Record<string, string> = {
  ERD_Booster_Pumps: "ERD Booster Pump",
  Air_Scour_Blower: "Air Scour Blower",
  White_Water_Pumps: "White Water Pumps",
  Backwash_Pumps: "Backwash Pumps",
  Seawater_intake_system: "Seawater Intake System",
  Cartridge_Filter_Pumps: "Cartridge Filter Pumps",
  HPP_Booster_pump: "HPP Booster Pump",
  HPP_Pressure_Pumps_HPP: "HPP Pressure Pumps",
  Second_Pass_Feed_Pumps: "Second Pass Feed Pumps",
  Product_Water_Pumps: "Product Water Pumps",
};

export const CHART_COLORS = {
  flowMeasured: "#1890FF",
  pumpPowerExpected: "#52C41A",
  pumpPowerMeasured: "#FAAD14",
  efficiency: "#F5222D",
  speed: "#722ED1",
};

export const DEFAULT_METRIC = "Flow";

export const DEFAULT_OPERATIONAL_METRICS = {
  metric1: "Flow_Measured",
  metric2: "Pump_Power_Expected",
  metric3: "Efficiency_Measured",
  metric4: "Head_Measured",
};

export const DEFAULT_PERFORMANCE_METRICS = {
  chart1: { metric1: "Flow_Measured", metric2: "Pump_Power_Expected" },
  chart2: { metric1: "Flow_Measured", metric2: "Efficiency_Measured" },
  chart3: { metric1: "Flow_Measured", metric2: "Pump_Power_Measured" },
};
