"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  ReactNode,
} from "react";
import { DateRangePickerType } from "@/types/common.types";

interface PumpAnalysisContextValue {
  siteName: string;
  dateRange: DateRangePickerType;
  activePumpTab: string;
  selectedPumpId: string;
  performancePumpId: string;
  setDateRange: (range: DateRangePickerType) => void;
  setActivePumpTab: (tab: string) => void;
  setSelectedPumpId: (pumpId: string) => void;
  setPerformancePumpId: (pumpId: string) => void;
}

const PumpAnalysisContext = createContext<PumpAnalysisContextValue | undefined>(
  undefined
);

interface PumpAnalysisProviderProps {
  children: ReactNode;
  siteName: string;
  initialDateRange: DateRangePickerType;
}

export const PumpAnalysisProvider: React.FC<PumpAnalysisProviderProps> = ({
  children,
  siteName,
  initialDateRange,
}) => {
  const [dateRange, setDateRange] =
    useState<DateRangePickerType>(initialDateRange);
  const [activePumpTab, setActivePumpTab] = useState<string>("");
  const [selectedPumpId, setSelectedPumpId] = useState<string>("");
  const [performancePumpId, setPerformancePumpId] = useState<string>("");

  const prevSiteNameRef = useRef<string>(siteName);

  // Reset state immediately when site changes
  useEffect(() => {
    if (prevSiteNameRef.current !== siteName) {
      console.log(
        "🔄 Site changed from",
        prevSiteNameRef.current,
        "to",
        siteName
      );

      // Immediately reset all state
      setActivePumpTab("");
      setSelectedPumpId("");
      setPerformancePumpId("");

      prevSiteNameRef.current = siteName;
    }
  }, [siteName]);

  const value: PumpAnalysisContextValue = {
    siteName,
    dateRange,
    activePumpTab,
    selectedPumpId,
    performancePumpId,
    setDateRange,
    setActivePumpTab,
    setSelectedPumpId,
    setPerformancePumpId,
  };

  return (
    <PumpAnalysisContext.Provider value={value}>
      {children}
    </PumpAnalysisContext.Provider>
  );
};

export const usePumpAnalysis = () => {
  const context = useContext(PumpAnalysisContext);
  if (!context) {
    throw new Error("usePumpAnalysis must be used within PumpAnalysisProvider");
  }
  return context;
};
