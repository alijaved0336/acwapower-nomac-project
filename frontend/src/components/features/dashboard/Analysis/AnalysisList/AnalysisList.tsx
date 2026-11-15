"use client";
import React from "react";
import { Card } from "antd";

import AnalysisHeader from "./AnalysisHeader";
import AnalysisFilters from "./AnalysisFilters";
import AnalysisTable from "./AnalysisTable";
import { AnalysisListProvider } from "../context/AnalysisListContext";

export default function AnalysisList() {
  return (
    <AnalysisListProvider>
      <AnalysisHeader />
      <div className="mt-8 px-16">
        <Card className="card">
          <AnalysisFilters />
          <AnalysisTable />
        </Card>
      </div>
    </AnalysisListProvider>
  );
}
