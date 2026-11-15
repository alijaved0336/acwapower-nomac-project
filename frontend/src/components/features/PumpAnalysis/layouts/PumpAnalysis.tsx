"use client";

import React, { useState, useEffect, useCallback } from "react";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import { usePumpData } from "../hooks/usePumpData";
import FilterBar from "../filters/FilterBar";
import PumpTabs from "../filters/PumpTabs";
import PumpIdTabs from "../filters/PumpIdTabs";
import OperationalTrendChart from "../charts/OperationalTrendChart";
import PerformanceTrendChart from "../charts/PerformanceTrendChart";
import LoadingSkeleton from "../filters/LoadingSkeleton";

const PumpAnalysis: React.FC = () => {
  const {
    siteName,
    dateRange,
    setDateRange,
    activePumpTab,
    setActivePumpTab,
    selectedPumpId,
    setSelectedPumpId,
  } = usePumpAnalysis();

  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [chartsLoaded, setChartsLoaded] = useState(false);

  const {
    pumpsData,
    pumpTabs,
    isLoading: pumpsLoading,
    getPumpList,
  } = usePumpData(siteName);

  const currentPumps = getPumpList(activePumpTab);

  const handlePumpTabChange = useCallback(
    (tab: string) => {
      setActivePumpTab(tab);
      setSelectedPumpId("");
      setChartsLoaded(false);
    },
    [setActivePumpTab, setSelectedPumpId]
  );

  const handlePumpIdChange = useCallback(
    (pumpId: string) => {
      setSelectedPumpId(pumpId);
      setChartsLoaded(false);
    },
    [setSelectedPumpId]
  );

  useEffect(() => {
    if (pumpTabs.length > 0 && !activePumpTab) {
      const firstTab = pumpTabs[0].key;
      setActivePumpTab(firstTab);
    }
  }, [pumpTabs, activePumpTab, setActivePumpTab]);

  useEffect(() => {
    if (currentPumps.length > 0 && activePumpTab && !selectedPumpId) {
      const firstPumpId = currentPumps[0].Pump_id;
      setSelectedPumpId(firstPumpId);
    }
  }, [currentPumps, activePumpTab, selectedPumpId, setSelectedPumpId]);

  useEffect(() => {
    if (pumpsData && activePumpTab && selectedPumpId) {
      setIsInitialLoad(false);
    }
  }, [pumpsData, activePumpTab, selectedPumpId]);

  const handleChartsLoaded = useCallback(() => {
    setChartsLoaded(true);
  }, []);

  if (pumpsLoading || !pumpsData || !activePumpTab || !selectedPumpId) {
    return <LoadingSkeleton />;
  }

  return (
    <div style={{ padding: "24px" }}>
      <FilterBar
        siteName={siteName}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        style={{ marginBottom: "16px" }}
      />

      <div style={{ marginBottom: "12px" }}>
        <PumpTabs
          activeTab={activePumpTab}
          onChange={handlePumpTabChange}
          tabs={pumpTabs}
        />
      </div>

      {currentPumps.length > 0 && (
        <div style={{ marginBottom: "24px" }}>
          <PumpIdTabs
            pumps={currentPumps}
            activeKey={selectedPumpId}
            onChange={handlePumpIdChange}
          />
        </div>
      )}

      <OperationalTrendChart
        key={`operational-${siteName}-${activePumpTab}-${selectedPumpId}-${dateRange?.[0]?.valueOf()}-${dateRange?.[1]?.valueOf()}`}
        isInitialLoad={isInitialLoad}
        onDataLoaded={handleChartsLoaded}
      />

      <PerformanceTrendChart
        key={`performance-${siteName}-${activePumpTab}-${selectedPumpId}-${dateRange?.[0]?.valueOf()}-${dateRange?.[1]?.valueOf()}`}
        isInitialLoad={isInitialLoad}
        onDataLoaded={handleChartsLoaded}
      />
    </div>
  );
};

export default PumpAnalysis;
