"use client";

import React, { useMemo } from "react";
import { Drawer, Button, Space } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import { DateRangePickerType } from "@/types/common.types";
import dayjs from "dayjs";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const { dateRange, setDateRange } = usePumpAnalysis();

  // ✅ Correctly typed default date range
  const defaultDateRange: DateRangePickerType = useMemo(
    () => [dayjs().subtract(7, "days"), dayjs()],
    []
  );

  const handleResetFilters = () => {
    setDateRange(defaultDateRange);
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
            value={dateRange ?? defaultDateRange}
            onChange={(range) => setDateRange(range as DateRangePickerType)}
            size="middle"
            disableFutureDates
            style={{ width: "100%" }}
          />
        </div>
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
