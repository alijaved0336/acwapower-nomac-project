import { Button, Space, Typography } from "antd";
import React, { useState } from "react";
import { PlusOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import CreateAnalysisModal from "../AnalysisTemplate/CreateAnalysisModal";
import Header from "../../../../layouts/DashboardLayout/Header";
import ThemeToggle from "../../../../layouts/DashboardLayout/ThemeToggle";
import CompactStatusBar, {
  ProfileSection,
} from "../../../../common/CompactStatusBar";

const AnalysisHeader = () => {
  return (
    <CompactStatusBar
      activeTab="all"
      onTabChange={() => {}}
      siteName=""
      showSite={false}
      dateRangeText=""
      customTabs={[]}
      showFilters={false}
      onFilterClick={() => {}}
      enableSiteSelection={true}
      siteOptions={[]}
      selectedSite={""}
      onSiteChange={() => {}}
    />
  );
};

export default AnalysisHeader;
