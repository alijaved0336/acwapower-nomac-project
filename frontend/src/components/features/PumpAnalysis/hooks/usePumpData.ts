import { useMemo } from "react";
import { useGetPumpsQuery } from "@/store/api/pumpAnalysisApi";
import { PUMP_CATEGORY_LABELS } from "../utils/constants";
import { formatPumpName } from "../utils/chartHelpers";

export const usePumpData = (siteName: string) => {
  const {
    data: pumpsData,
    isLoading,
    error,
  } = useGetPumpsQuery({ siteName }, { skip: !siteName });

  const pumpTabs = useMemo(() => {
    if (!pumpsData) return [];
    return Object.keys(pumpsData).map((key) => ({
      key,
      label: PUMP_CATEGORY_LABELS[key] || formatPumpName(key),
    }));
  }, [pumpsData]);

  const getPumpList = (activePumpTab: string) => {
    if (!pumpsData || !activePumpTab) return [];
    return pumpsData[activePumpTab] || [];
  };

  const getPumpOptions = (activePumpTab: string) => {
    const pumps = getPumpList(activePumpTab);
    return pumps.map((pump) => ({
      label: `${formatPumpName(pump.pump)} (KKS: ${pump.Pump_id})`,
      value: pump.Pump_id,
    }));
  };

  return {
    pumpsData,
    pumpTabs,
    isLoading,
    error,
    getPumpList,
    getPumpOptions,
  };
};
