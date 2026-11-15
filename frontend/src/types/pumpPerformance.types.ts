import { Dayjs } from "dayjs";

export interface MetricData {
  label: string;
  value: number | null;
  unit: string;
  trend?: "up" | "down";
}

export interface PumpKPI {
  id: string;
  attribute: string;
  unit: string;
  [key: string]: any;
  isKKSRow?: boolean;
}

export interface ActionRecordDisplay {
  id: string;
  pumpName: string;
  action: string;
  dateTime: string;
}

export interface PumpPerformanceContextType {
  siteId: string;
  selectedDate: Dayjs | null;
  dateRange: [Dayjs, Dayjs] | null;
  selectedCategory: string;
  activeTab: string;
  selectedPumps: string[];
  pumpCategories: Array<{ id: string; name: string }>;
  isTabChanging: boolean;
  setSelectedDate: (date: Dayjs | null) => void;
  setDateRange: (dates: [Dayjs, Dayjs] | null) => void;
  setSelectedCategory: (category: string) => void;
  setActiveTab: (tab: string) => void;
  setSelectedPumps: (pumps: string[]) => void;
  cardsData: any;
  kpiData: any;
  actionsData: any;
  cardsLoading: boolean;
  kpisLoading: boolean;
  actionsLoading: boolean;
  isError: boolean;
  error: any;
}
