export type RefreshInterval =
  | "off"
  // | "5s"
  | "10s"
  | "30s"
  | "1m"
  | "5m"
  | "15m"
  | "30m"
  | "1h"
  | "2h"
  | "1d";

export interface RefreshIntervalConfig {
  value: RefreshInterval;
  label: string;
  milliseconds: number;
}

export const REFRESH_INTERVALS: Record<RefreshInterval, RefreshIntervalConfig> =
  {
    off: { value: "off", label: "Off", milliseconds: 0 },
    //   "5s": { value: "5s", label: "5s", milliseconds: 5 * 1000 }, //Too Short for UI
    "10s": { value: "10s", label: "10s", milliseconds: 10 * 1000 },
    "30s": { value: "30s", label: "30s", milliseconds: 30 * 1000 },
    "1m": { value: "1m", label: "1m", milliseconds: 60 * 1000 },
    "5m": { value: "5m", label: "5m", milliseconds: 5 * 60 * 1000 },
    "15m": { value: "15m", label: "15m", milliseconds: 15 * 60 * 1000 },
    "30m": { value: "30m", label: "30m", milliseconds: 30 * 60 * 1000 },
    "1h": { value: "1h", label: "1h", milliseconds: 60 * 60 * 1000 },
    "2h": { value: "2h", label: "2h", milliseconds: 2 * 60 * 60 * 1000 },
    "1d": { value: "1d", label: "1d", milliseconds: 24 * 60 * 60 * 1000 },
  };

export const getRefreshIntervalLabel = (
  interval: RefreshInterval | undefined | null
): string => {
  if (!interval || !REFRESH_INTERVALS[interval]) {
    return "Off";
  }
  return REFRESH_INTERVALS[interval].label;
};

export const getRefreshIntervalMs = (
  interval: RefreshInterval | undefined | null
): number => {
  if (!interval || !REFRESH_INTERVALS[interval]) {
    return 0;
  }
  return REFRESH_INTERVALS[interval].milliseconds;
};

export const isValidRefreshInterval = (
  interval: any
): interval is RefreshInterval => {
  return (
    interval && typeof interval === "string" && interval in REFRESH_INTERVALS
  );
};
