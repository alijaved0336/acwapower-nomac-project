export const PUMP_CARD_CONFIG = {
  METRICS: [
    {
      key: "sec_kwh_m3",
      label: "Overall SEC",
      unit: "Kwh/m3 (%)",
      showTrend: false,
      decimalPlaces: 0,
    },
    {
      key: "power_kw",
      label: "Total Power",
      unit: "KW",
      showTrend: true,
      decimalPlaces: 0,
    },
    {
      key: "flow_m3_hr",
      label: "Total Flow",
      unit: "m3/h",
      showTrend: false,
      decimalPlaces: 0,
    },
    {
      key: "load_kw_m3",
      label: "Load",
      unit: "%",
      showTrend: true,
      decimalPlaces: 2,
    },
  ] as const,

  FORMATTING: {
    DEFAULT_DECIMAL_PLACES: 0,
    EMPTY_VALUE: "-",
  },

  TREND_TYPES: {
    UP: "up",
    DOWN: "down",
    INSUFFICIENT: "insufficient",
  } as const,
};

export type MetricKey = (typeof PUMP_CARD_CONFIG.METRICS)[number]["key"];
export type TrendType =
  (typeof PUMP_CARD_CONFIG.TREND_TYPES)[keyof typeof PUMP_CARD_CONFIG.TREND_TYPES];

export interface MetricConfig {
  key: string;
  label: string;
  unit: string;
  showTrend: boolean;
  decimalPlaces: number;
}

export interface MetricData {
  label: string;
  value: number | null;
  unit: string;
  isModified?: boolean;
  trend?: TrendType;
  showTrend: boolean;
  decimalPlaces: number;
}
