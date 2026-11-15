"use client";

import React from "react";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import { Flex, Typography, Grid } from "antd";
import { DateRangePickerType } from "@/types/common.types";
import { filterBarFlexStyle, filterBarTitleStyle } from "../utils/styles";

const { useBreakpoint } = Grid;

interface FilterBarProps {
  siteName: string;
  dateRange: DateRangePickerType;
  onDateRangeChange: (range: DateRangePickerType) => void;
  style?: React.CSSProperties;
}

const FilterBar: React.FC<FilterBarProps> = ({
  siteName,
  dateRange,
  onDateRangeChange,
  style,
}) => {
  const size = useBreakpoint();
  const isMobile = !!size.xs;

  return (
    <Flex
      align="center"
      justify="space-between"
      wrap="wrap"
      gap={12}
      style={{
        ...filterBarFlexStyle(isMobile),
        ...style,
      }}
    >
      <Typography.Text style={filterBarTitleStyle(isMobile)}>
        {siteName} Pump Analysis
      </Typography.Text>

      <DateRangePicker
        value={dateRange}
        onChange={onDateRangeChange}
        disableFutureDates
        size="middle"
      />
    </Flex>
  );
};

export default FilterBar;
