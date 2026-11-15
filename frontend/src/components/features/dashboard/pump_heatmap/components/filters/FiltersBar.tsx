import React, { FC } from "react";
import { Flex, Typography } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import dayjs, { Dayjs } from "dayjs";
import { DateRangePickerType } from "@/types/common.types";

const { Title } = Typography;

type FiltersBarProps = {
  screenTitle: string;
  dateRange?: DateRangePickerType;
  onDateRangeChange?: (dates: DateRangePickerType) => void;
};

const FiltersBar: FC<FiltersBarProps> = ({
  screenTitle,
  dateRange,
  onDateRangeChange,
}) => {
  const handleDateChange = (dates: DateRangePickerType) => {
    if (onDateRangeChange) {
      onDateRangeChange(dates);
    }
  };

  return (
    <Flex justify="space-between" align="center" style={{ padding: "0px 8px" }}>
      <Title
        level={3}
        style={{
          margin: 0,
          fontWeight: 500,
          paddingLeft: "8px",
          fontSize: "35px",
        }}
      >
        {screenTitle}
      </Title>

      <DateRangePicker
        value={dateRange}
        onChange={handleDateChange}
        disableFutureDates={true}
        size="middle"
      />
    </Flex>
  );
};

export default FiltersBar;
