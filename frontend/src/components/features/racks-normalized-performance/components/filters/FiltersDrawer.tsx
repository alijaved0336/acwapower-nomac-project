"use client";

import React, { useMemo } from "react";
import { Drawer, Button, Space, Divider } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import { useRacksNormalizedPerformanceContext } from "../../context/RacksNormalizedPerformanceContext";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import dayjs from "dayjs";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const { selectedFilters, selectedSite, handleFilterChange } =
    useRacksNormalizedPerformanceContext();

  const defaultDateRange = useMemo(
    () => [dayjs().subtract(7, "day"), dayjs()],
    []
  );

  const handleResetFilters = () => {
    handleFilterChange("dateRange", defaultDateRange);
  };

  return (
    <Drawer
      title="Filters"
      placement="right"
      onClose={onClose}
      open={open}
      width={360}
      extra={
        <Button onClick={handleResetFilters} size="small">
          Reset All
        </Button>
      }
    >
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* Date Range */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Date Range
          </label>
          <DateRangePicker
            value={selectedFilters.dateRange}
            onChange={(range) => handleFilterChange("dateRange", range)}
            size="middle"
            disableFutureDates
            style={{ width: "100%" }}
          />
        </div>

        <Divider style={{ margin: 0 }} />

        {/* Site Info (Read-only) */}
        <div>
          <div
            style={{
              padding: "12px",
              background: "#e6f7ff",
              borderRadius: "6px",
              border: "1px solid #91d5ff",
            }}
          >
            <p style={{ margin: 0, fontSize: "13px", color: "#666" }}>
              <strong>Site:</strong>{" "}
              {selectedSite ? getSiteDisplayName(selectedSite) : "Not selected"}
            </p>
            <p style={{ margin: "4px 0 0 0", fontSize: "11px", color: "#999" }}>
              Change site from Plant Overview page
            </p>
          </div>
        </div>
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
