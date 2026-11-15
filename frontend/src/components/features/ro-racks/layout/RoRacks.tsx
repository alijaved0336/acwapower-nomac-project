"use client";

import React from "react";
import { RoRacksProvider } from "../context/RoRacksContext";
import Filters from "../components/filters/Filters";
import RoRacksAllLayout from "./RoRacksAllLayout";

const RoRacksContent = () => {
  return (
    <div className="!space-y-24 !py-16">
      <Filters />
      <RoRacksAllLayout />
    </div>
  );
};

const RoRacks = () => (
  <RoRacksProvider>
    <RoRacksContent />
  </RoRacksProvider>
);

export default RoRacks;
