"use client";
import React, { memo } from "react";

import SidebarPanel from "@/components/features/dashboard/Analysis/AnalysisTemplate/Sidebar/SidebarPanel";
import { AnalysisTemplateProviderWithSuspense } from "../context/AnalysisTemplateContext";

import AnalysisTemplateHeader from "./AnalysisTemplateHeader";
import AddWidgetModal from "./AddWidgetModal";
import WidgetList from "./WidgetList/WidgetList";
import AnalysisTemplateFilters from "./AnalysisTemplateFilters";

const AnalysisTemplate = () => {
  return (
    <AnalysisTemplateProviderWithSuspense>
      <AnalysisTemplateHeader />
      <div className="mt-8 flex max-w-full items-start gap-16 px-12">
        <div className="max-w-[calc(100%-350px)] grow">
          <AnalysisTemplateFilters />
          <WidgetList />
        </div>
        <SidebarPanel />
      </div>
      <AddWidgetModal />
    </AnalysisTemplateProviderWithSuspense>
  );
};

export default memo(AnalysisTemplate);
