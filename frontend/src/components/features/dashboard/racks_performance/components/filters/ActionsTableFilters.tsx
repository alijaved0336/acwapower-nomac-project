import React, { FC } from "react";
import { Filter } from "lucide-react";
import { Select, theme } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import { Dayjs } from "dayjs";
import { DateRangePickerType } from "../../../../../../types/common.types";

interface ActionsTableFiltersProps {
  showFilter: boolean;
  setShowFilter: (show: boolean) => void;
  selectedPumps: string[];
  setSelectedPumps: (pumps: string[]) => void;
  dateRange: DateRangePickerType;
  setDateRange: (dates: DateRangePickerType) => void;
  selectedDate: Dayjs | null;
  filterData: any;
}

export const ActionsTableFilters: FC<ActionsTableFiltersProps> = ({
  showFilter,
  setShowFilter,
  selectedPumps,
  setSelectedPumps,
  dateRange,
  setDateRange,
  selectedDate,
  filterData,
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
      style={{
        display: "flex",
        gap: "12px",
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <button
        onClick={() => setShowFilter(!showFilter)}
        style={{
          padding: "6px 12px",
          backgroundColor: showFilter
            ? token.colorPrimaryBg
            : token.colorBgContainer,
          border: `1px solid ${showFilter ? token.colorPrimary : token.colorBorder}`,
          borderRadius: "6px",
          fontSize: "14px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "6px",
          color: showFilter ? token.colorPrimary : token.colorText,
          fontWeight: 400,
          transition: "all 0.2s ease",
          blockSize: 31,
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
        />
      )}

      <DateRangePicker
        value={displayValue as [Dayjs, Dayjs] | null}
        onChange={handleDateChange}
        disableFutureDates={false}
        style={{ width: 360 }}
        size="middle"
      />
    </div>
  );
};
