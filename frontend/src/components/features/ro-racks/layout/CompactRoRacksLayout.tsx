"use client";

import React, { useMemo, useRef, useEffect, useState } from "react";
import dayjs from "dayjs";
import { useRoRacksContext } from "../context/RoRacksContext";
import {
  CompactFiltersDrawer,
  CompactLayout,
  CompactSection,
  CompactStatusBar,
  type TabType,
} from "@/components/common";
import { PAGE_LAYOUTS } from "@/utils/layoutUtils";
import Select from "@/components/common/widgets/Select";
import { getSiteDisplayName } from "../../../../utils/siteDisplayNames";
import CompactRoQualityCards from "../components/CompactRoQualityCards";
import CompactRoRacksChart from "../components/CompactRoRacksChart";
import CompactRoRacksTable from "../components/CompactRoRacksTable";
import CompactRoOperationalStatusTable from "../components/CompactRoOperationalStatusTable";
import layoutStyles from "../styles/compactRoRacksLayout.module.css";
import { cn } from "@/utils/cn";
import { Button, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import { useGetRoRacksTableQuery } from "@/store/api/roRacksApi";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "@/utils/chartExport";

const CompactRoRacksLayoutContent: React.FC = () => {
  const {
    selectedFilters,
    selectedSite,
    handleFilterChange,
    isLoadingOverall,
  } = useRoRacksContext();

  const [activeTab, setActiveTab] = useState<"firstPass" | "secondPass">(
    "firstPass"
  );

  const hasLoadedOnce = useRef(false);

  useEffect(() => {
    if (hasLoadedOnce.current && !isLoadingOverall) {
      hasLoadedOnce.current = true;
    }
  }, [isLoadingOverall]);

  // No active filters needed since site is in the header and date is in status bar
  const activeFilters = useMemo(() => {
    return [];
  }, []);

  // Custom tabs configuration
  const customTabs = useMemo(
    () => [
      {
        key: "firstPass" as const,
        label: "",
        icon: (
          <span
            className={cn(
              layoutStyles.tabIcon,
              activeTab === "firstPass"
                ? layoutStyles.tabIconActive
                : layoutStyles.tabIconInactive
            )}
          >
            1st Pass
          </span>
        ),
      },
      {
        key: "secondPass" as const,
        label: "",
        icon: (
          <span
            className={cn(
              layoutStyles.tabIcon,
              activeTab === "secondPass"
                ? layoutStyles.tabIconActive
                : layoutStyles.tabIconInactive
            )}
          >
            2nd Pass
          </span>
        ),
      },
    ],
    [activeTab]
  );

  // Render content based on active tab
  const renderTabContent = () => {
    return (
      <>
        {/* Row 1: Quality cards (3 for Jubail, 9 for UAQ) */}
        <div className={layoutStyles.qualityCardsRow}>
          <CompactRoQualityCards pass={activeTab} />
        </div>

        {/* Row 2: Chart and operational status table side by side */}
        <div className={layoutStyles.chartTableRow}>
          <div className={layoutStyles.chartWrapper}>
            <CompactSection
              colorKey={activeTab === "firstPass" ? "firstPass" : "secondPass"}
            >
              <CompactRoRacksChart pass={activeTab} />
            </CompactSection>
          </div>
          <div className={layoutStyles.operationalStatusWrapper}>
            <CompactSection colorKey="overall">
              <CompactRoOperationalStatusTable pass={activeTab} />
            </CompactSection>
          </div>
        </div>

        {/* Row 3: Racks Performance table */}
        <div className={layoutStyles.racksTableRow}>
          <CompactSection
            colorKey="overall"
            // customHeader={
            //   <div
            //     style={{
            //       display: "flex",
            //       alignItems: "center",
            //       justifyContent: "space-between",
            //       width: "100%",
            //     }}
            //   >
            //     <span style={{ fontWeight: 600 }}>Racks Performance</span>
            //     <RacksPerformanceDownloadButton pass={activeTab} />
            //   </div>
            // }
          >
            <CompactRoRacksTable pass={activeTab} />
          </CompactSection>
        </div>
      </>
    );
  };

  const needsSecondaryTabs = useMemo(() => {
    if (!customTabs) return false;
    return customTabs.length > 4;
  }, [customTabs]);

  const isInitialLoading = !hasLoadedOnce.current && isLoadingOverall;

  // Get the label for the selected date
  const getDateLabel = () => {
    if (!selectedFilters.selectedDate) return "Select Date";

    const today = dayjs().startOf("day");
    const yesterday = dayjs().subtract(1, "day").startOf("day");
    const weekStart = dayjs().startOf("week");

    if (selectedFilters.selectedDate.isSame(today, "day")) {
      return "Today";
    } else if (selectedFilters.selectedDate.isSame(yesterday, "day")) {
      return "Yesterday";
    } else if (selectedFilters.selectedDate.isSame(weekStart, "day")) {
      return "This Week";
    }

    return selectedFilters.selectedDate.format("MMM DD, YYYY");
  };

  return (
    <div>
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={(tab: TabType) => {
          if (tab === "firstPass" || tab === "secondPass") {
            setActiveTab(tab);
          }
        }}
        siteName={
          selectedSite
            ? getSiteDisplayName(selectedSite)
            : getSiteDisplayName(selectedFilters.plant) || "No Plant Selected"
        }
        dateRangeText=""
        activeFilters={activeFilters}
        customTabs={customTabs}
        loading={isInitialLoading}
        showSecondaryTabs={needsSecondaryTabs}
        maxPrimaryTabs={4}
        showFilters={false}
        showActiveFilters={false}
      >
        {/* Custom Date Select Component in Status Bar */}
        <Select
          value={selectedFilters.selectedDate?.format("YYYY-MM-DD") || ""}
          onChange={(value) => {
            if (value === "today") {
              handleFilterChange("selectedDate", dayjs().startOf("day"));
            } else if (value === "yesterday") {
              handleFilterChange(
                "selectedDate",
                dayjs().subtract(1, "day").startOf("day")
              );
            } else if (value === "week") {
              handleFilterChange("selectedDate", dayjs().startOf("week"));
            }
          }}
          options={[
            { value: "today", label: "Today" },
            { value: "yesterday", label: "Yesterday" },
            { value: "week", label: "Day Before Yesterday" },
          ]}
          displayKey="label"
          valueKey="value"
          placeholder="Select Date"
          size="middle"
          style={{
            width: 140,
            height: 40,
            marginRight: "100px",
          }}
        />
      </CompactStatusBar>

      <div className="px-sm grid h-[calc(100vh-56px)] grid-cols-6 grid-rows-[min-content_0.75fr_1.25fr] gap-8 p-8">
        {renderTabContent()}
      </div>
    </div>
  );
};

// Download button component for Racks Performance table
const RacksPerformanceDownloadButton: React.FC<{
  pass: "firstPass" | "secondPass";
}> = ({ pass }) => {
  const { selectedFilters, selectedSite } = useRoRacksContext();
  const site_name = selectedSite || selectedFilters?.plant;
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");

  const { data } = useGetRoRacksTableQuery(
    { site_name, selectedDate, pass },
    { skip: !site_name || !selectedDate }
  );

  const tableData = useMemo(() => {
    if (!data?.data?.table?.length) return [];
    const rowCount = data.data.table[0]?.dataSource?.length ?? 0;
    const rows: any[] = [];

    for (let i = 0; i < rowCount; i++) {
      const row: any = { key: `rack-${i}` };
      data.data.table.forEach((col: any) => {
        row[col.columnName] = col.dataSource?.[i] ?? null;
      });
      rows.push(row);
    }

    return rows;
  }, [data]);

  const handleDownload = (format: "csv" | "excel") => {
    if (!tableData || tableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const passLabel = pass === "firstPass" ? "1st_pass" : "2nd_pass";
    const filename = getFilenameFromTitle(`${passLabel}_racks_performance`);

    // Create columns from table data keys
    const columns = Object.keys(tableData[0] || {})
      .filter((key) => key !== "key")
      .map((key) => ({
        title: key,
        dataIndex: key,
      }));

    if (format === "csv") {
      exportTableToCSV(tableData, columns as any, filename);
    } else {
      exportTableToExcel(tableData, columns as any, filename);
    }
  };

  const downloadMenuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Download as CSV",
      onClick: () => handleDownload("csv"),
      disabled: !tableData || tableData.length === 0,
    },
    {
      key: "excel",
      label: "Download as Excel",
      onClick: () => handleDownload("excel"),
      disabled: !tableData || tableData.length === 0,
    },
  ];

  const moreMenuItems: MenuProps["items"] = [
    {
      key: "download",
      type: "submenu",
      label: "Download",
      children: downloadMenuItems,
    },
  ];

  return (
    <Dropdown menu={{ items: moreMenuItems }} trigger={["click"]}>
      <Button icon={<MoreOutlined />} size="small" style={{ height: "24px" }} />
    </Dropdown>
  );
};

const CompactRoRacksLayout: React.FC = () => <CompactRoRacksLayoutContent />;

export default CompactRoRacksLayout;
