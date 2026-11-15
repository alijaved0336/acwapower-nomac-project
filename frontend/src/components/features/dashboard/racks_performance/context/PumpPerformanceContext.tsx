"use client";

import React, { createContext, useContext, ReactNode } from "react";
import { Dayjs } from "dayjs";
import { usePumpPerformanceState } from "./usePumpPerformanceState";
import { DateRangePickerType } from "../../../../../types/common.types";

interface PumpPerformanceContextType {
  siteId: string;
  selectedDate: Dayjs | null;
  dateRange: DateRangePickerType;
  selectedCategory: string;
  activeTab: string;
  selectedPumps: string[];
  pumpCategories: Array<{ id: string; name: string }>;
  isTabChanging: boolean;
  setSelectedDate: (date: Dayjs | null) => void;
  setDateRange: (dates: DateRangePickerType) => void;
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
const PumpPerformanceContext = createContext<
  PumpPerformanceContextType | undefined
>(undefined);

export const usePumpPerformance = () => {
  const context = useContext(PumpPerformanceContext);
  if (!context) {
    throw new Error(
      "usePumpPerformance must be used within PumpPerformanceProvider"
    );
  }
  return context;
};

interface ProviderProps {
  children: ReactNode;
  siteId: string;
}

export const PumpPerformanceProvider: React.FC<ProviderProps> = ({
  children,
  siteId,
}) => {
  const contextValue = usePumpPerformanceState(siteId);

  return (
    <PumpPerformanceContext.Provider value={contextValue}>
      {children}
    </PumpPerformanceContext.Provider>
  );
};
