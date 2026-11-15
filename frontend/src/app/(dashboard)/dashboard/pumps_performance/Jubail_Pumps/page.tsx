import React from "react";
import PumpPerformanceLayout from "@/components/features/dashboard/racks_performance/layouts/PumpPerformanceLayout";
import { SITE_ID_MAP } from "@/components/features/dashboard/racks_performance/utils/pumpPerformanceData";

export default function JubailPumpsPage() {
  return <PumpPerformanceLayout defaultSiteId={SITE_ID_MAP.JUBAIL} />;
}
