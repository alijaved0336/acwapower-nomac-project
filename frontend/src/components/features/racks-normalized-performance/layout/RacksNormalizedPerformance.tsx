"use client";

import React from "react";
import { RacksNormalizedPerformanceProvider } from "../context/RacksNormalizedPerformanceContext";
import RacksNormalizedPerformanceAllLayout from "./CompactRacksNormalizedPerformanceLayout";

const RacksNormalizedPerformanceContent = () => {
  return (
    <div className="!space-y-24">
      <RacksNormalizedPerformanceAllLayout />
    </div>
  );
};

const RacksNormalizedPerformance = () => (
  <RacksNormalizedPerformanceProvider>
    <RacksNormalizedPerformanceContent />
  </RacksNormalizedPerformanceProvider>
);

export default RacksNormalizedPerformance;
