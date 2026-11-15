// src/components/common/CommonDashboardFilters/types.ts
import { Dayjs } from "dayjs";

export interface FilterConfig {
  cluster?: boolean;
  plant?: boolean;
  rack?: boolean;
  area?: boolean;
  chemical?: boolean;
  dateRange?: boolean;
  stream?: boolean;
}

export interface FilterValues {
  cluster?: string;
  plant?: string;
  rack?: string | number | string[] | number[];
  area?: string;
  chemical?: string;
  dateRange?: [Dayjs, Dayjs];
  stream?: string;
}

export interface FilterChangeHandler {
  (key: keyof FilterValues, value: any): void;
}

export interface CommonDashboardFiltersProps {
  config: FilterConfig;
  values: FilterValues;
  onChange: FilterChangeHandler;
  className?: string;
  disabled?: boolean;
}
