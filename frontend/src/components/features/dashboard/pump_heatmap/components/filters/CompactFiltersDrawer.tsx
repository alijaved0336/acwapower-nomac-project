"use client";

import React from "react";
import { Drawer, Space, Button } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import { usePumpHeatmapContext } from "../../context/pumpHeatmapContext";
import dayjs from "dayjs";

interface CompactFiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const CompactFiltersDrawer: React.FC<CompactFiltersDrawerProps> = ({
  open,
  onClose,
}) => {
  const { dateRange, handleDateRangeChange } = usePumpHeatmapContext();

  const handleResetFilters = () => {
    const defaultFromDate = dayjs().subtract(7, "days").startOf("day");
    const defaultToDate = dayjs().endOf("day");
    if (handleDateRangeChange) {
      handleDateRangeChange([defaultFromDate, defaultToDate]);
    }
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
            value={dateRange}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1] && handleDateRangeChange) {
                handleDateRangeChange([dates[0], dates[1]]);
              }
            }}
            disableFutureDates={true}
            size="middle"
            style={{ width: "100%" }}
          />
        </div>
      </Space>
    </Drawer>
  );
};

export default CompactFiltersDrawer;
