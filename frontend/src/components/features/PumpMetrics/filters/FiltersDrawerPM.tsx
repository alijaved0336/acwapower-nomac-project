"use client";

import React, { useMemo } from "react";
import { Drawer, Button, Space } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import dayjs from "dayjs";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawerPM: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const { selectedFilters, handleFilterChange } = usePumpMetricsContext();

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
      </Space>
    </Drawer>
  );
};

export default FiltersDrawerPM;
