"use client";

import React, { useMemo } from "react";
import { Drawer, Button, Space, Divider, DatePicker } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import Select from "@/components/common/widgets/Select";
import MultiSelect from "@/components/common/widgets/MultiSelect";
import { useAlertsOverviewContext } from "../context/AlertsOverviewContext";
import dayjs from "dayjs";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import styles from "../styles/filtersDrawer.module.css";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const {
    selectedFilters,
    selectedSite,

    handleFilterChange,
  } = useAlertsOverviewContext();

  const defaultDateRange = useMemo(
    () => [dayjs().subtract(7, "day"), dayjs()],
    []
  );

  const isUAQSelected = selectedSite?.toLowerCase().includes("uaq");

  const handleResetFilters = () => {
    handleFilterChange("plant", "");
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
      <Space direction="vertical" size="large" className={styles.drawerContent}>
        {/* Date Range */}
        <div className={styles.filterSection}>
          <label className={styles.filterLabel}>Date</label>
          <DateRangePicker
            value={selectedFilters.dateRange}
            onChange={(range) => handleFilterChange("dateRange", range)}
            size="middle"
            disableFutureDates
            style={{ width: "100%" }}
          />
        </div>

        <Divider className={styles.divider} />

        {/* Cluster and Plant filters are hidden - controlled globally from Plant Overview */}
        <div className={styles.filterSection}>
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

        <Divider className={styles.divider} />
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
