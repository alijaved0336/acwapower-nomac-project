"use client";

import React, { FC, memo } from "react";
import { Filter } from "lucide-react";
import { Select, theme } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import { Dayjs } from "dayjs";
import { DateRangePickerType } from "../../../../../../types/common.types";
import { formatString } from "../../../../../../utils/helpers";

interface ActionsPerformanceFiltersProps {
  selectedPump?: string;
  showFilter: boolean;
  setShowFilter: (show: boolean) => void;
  selectedPumps: string[];
  setSelectedPumps: (pumps: string[]) => void;
  dateRange: DateRangePickerType;
  setDateRange: (dates: DateRangePickerType) => void;
  selectedDate: Dayjs | null;
  filterData: any;
  actionsLoading?: boolean;
}

const ActionsPerformanceFilters: FC<ActionsPerformanceFiltersProps> = ({
  selectedPump,
  showFilter,
  setShowFilter,
  selectedPumps,
  setSelectedPumps,
  dateRange,
  setDateRange,
  selectedDate,
  filterData,
  actionsLoading,
}) => {
  const { token } = theme.useToken();

  const handleDateChange = (dates: DateRangePickerType) => {
    if (dates && dates[0] && dates[1]) {
      setDateRange(dates);
    } else {
      setDateRange(null);
    }
  };

  const displayValue =
    dateRange || (selectedDate ? [selectedDate, null] : null);

  return (
    <div
      className="rounded-md p-3"
      style={{
        backgroundColor: token.colorBgContainer,
        border: `1px solid ${token.colorBorder}`,
        boxShadow: `0 2px 8px ${token.colorFillQuaternary}`,
      }}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left side - Title */}
        <div className="flex items-center gap-2">
          <span
            className="text-sm font-semibold"
            style={{ color: token.colorText }}
          >
            {formatString(selectedPump ?? "") || "Actions Overview"}
          </span>
        </div>

        {/* Right side - Filters */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilter(!showFilter)}
            disabled={actionsLoading}
            style={{
              padding: "6px 12px",
              backgroundColor: showFilter
                ? token.colorPrimaryBg
                : token.colorBgContainer,
              border: `1px solid ${showFilter ? token.colorPrimary : token.colorBorder}`,
              borderRadius: "6px",
              fontSize: "14px",
              cursor: actionsLoading ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              color: showFilter ? token.colorPrimary : token.colorText,
              fontWeight: 400,
              transition: "all 0.2s ease",
              blockSize: 31,
              opacity: actionsLoading ? 0.5 : 1,
            }}
          >
            <Filter size={14} />
            Filter
          </button>

          {showFilter && filterData && (
            <Select
              mode="multiple"
              allowClear
              placeholder="Select pumps"
              value={selectedPumps}
              onChange={setSelectedPumps}
              options={filterData.pumps}
              style={{ minWidth: 250, maxWidth: 400 }}
              maxTagCount={2}
              maxTagPlaceholder={(omitted) => `+${omitted.length} more`}
              showSearch
              disabled={actionsLoading}
            />
          )}

          <DateRangePicker
            value={displayValue as [Dayjs, Dayjs] | null}
            onChange={handleDateChange}
            disableFutureDates={false}
            style={{ width: 360 }}
            size="middle"
            disabled={actionsLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default memo(ActionsPerformanceFilters);
