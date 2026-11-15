"use client";

import React from "react";
import AlertsLayout from "./layouts/AlertsLayout";
import { AlertsOverviewProvider } from "./context/AlertsOverviewContext";

const Alerts = () => (
  <AlertsOverviewProvider>
    <AlertsLayout />
  </AlertsOverviewProvider>
);

export default Alerts;
