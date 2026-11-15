"use client";

import React from "react";
import { RacksWeightedProvider } from "../context/RacksWeightedContext";
import CompactRacksWeightedLayout from "../layouts/CompactRacksWeightedLayout";

const RacksWeighted = () => (
  <RacksWeightedProvider>
    <CompactRacksWeightedLayout />
  </RacksWeightedProvider>
);

export default RacksWeighted;
