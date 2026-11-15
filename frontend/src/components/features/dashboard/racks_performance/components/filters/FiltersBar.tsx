"use client";
import React, { FC } from "react";
import { Flex, Typography, DatePicker } from "antd";
import dayjs, { Dayjs } from "dayjs";
import { customLocale } from "@/utils/datePickerUtil";

import { DateFormat } from "../../../../../../constants/enums";

const { Title } = Typography;

interface FiltersBarProps {
  screenTitle: string;
  selectedDate?: Dayjs | null;
  onDateChange?: (date: Dayjs | null) => void;
}

const FiltersBar: FC<FiltersBarProps> = ({
  screenTitle,
  selectedDate,
  onDateChange,
}) => {
  const handleDateChange = (date: Dayjs | null) => {
    if (onDateChange) {
      if (date) {
        const utcDate = dayjs.utc(date.format("YYYY-MM-DD HH:mm:ss"));
        onDateChange(utcDate);
      } else {
        onDateChange(null);
      }
    }
  };

  return (
    <Flex
      justify="space-between"
      align="center"
      style={{ padding: "24px 16px" }}
    >
      <Title level={3} style={{ margin: 0, fontWeight: 500, fontSize: "35px" }}>
        {screenTitle}
      </Title>
      <DatePicker
        showTime={{
          format: "HH:mm:ss",
        }}
        width="220px"
        value={selectedDate}
        onChange={handleDateChange}
        placeholder="Select date & time"
        format={DateFormat.DATE_TIME_24H}
        style={{ width: 210 }}
        locale={customLocale}
      />
    </Flex>
  );
};

export default FiltersBar;
