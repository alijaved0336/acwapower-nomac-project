"use client";

import React from "react";
import { AlertsOverviewProvider } from "../context/AlertsOverviewContext";
import SignalsLayout from "../layouts/SignalAssetLayout";

const Signals = () => (
  <AlertsOverviewProvider>
    <SignalsLayout />
  </AlertsOverviewProvider>
);

export default Signals;
