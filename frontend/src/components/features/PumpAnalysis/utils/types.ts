export interface PumpTab {
  key: string;
  label: string;
}

export interface PumpData {
  pump: string;
  Pump_id: string;
}

export interface OperationalColumnData {
  columnName: string;
  columnType: string;
  tableName: string;
  siteName: string;
  dataSource: (string | number)[];
}

export interface PerformanceColumnData {
  columnName: string;
  columnType: string;
  tableName: string;
  siteName: string;
  dataSource: (string | number)[];
}

export interface ChartMetrics {
  metric1: string;
  metric2: string;
  setMetric1: (value: string) => void;
  setMetric2: (value: string) => void;
}

export interface SpeedControl {
  speed: string | undefined;
  setSpeed: (value: string | undefined) => void;
  speedOptions: Array<{ label: string; value: string }>;
}
