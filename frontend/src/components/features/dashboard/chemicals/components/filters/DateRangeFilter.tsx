"use client";
import React, { memo } from "react";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import dayjs, { Dayjs } from "dayjs";

interface DateRangeFilterProps {
  dates: { from_date: string | null; to_date: string | null } | null;
  setDates: (
    dateRange: { from_date: string | null; to_date: string | null } | null
  ) => void;
}

const DateRangeFilter: React.FC<DateRangeFilterProps> = memo(
  ({ dates, setDates }) => {
    const getFormattedDate = (date: Dayjs | null, format: string) =>
      date ? dayjs(date).format(format) : null;

    const formatDateRange = (
      dates: [Dayjs | null, Dayjs | null] | null
    ): { from_date: string | null; to_date: string | null } | null => {
      if (!dates) return null;

      const [fromDate, toDate] = dates;
      return {
        from_date: getFormattedDate(fromDate, "YYYY-MM-DD HH:mm:ss"),
        to_date: getFormattedDate(toDate, "YYYY-MM-DD HH:mm:ss"),
      };
    };

    const handleDatesChange = (
      newDates: [Dayjs | null, Dayjs | null] | null
    ) => {
      const formattedDates = formatDateRange(newDates);
      setDates(formattedDates);
    };

    return (
      <DateRangePicker
        onChange={handleDatesChange}
        size="middle"
        value={
          dates?.from_date && dates?.to_date
            ? [
                dayjs(dates.from_date, "YYYY-MM-DD HH:mm:ss"),
                dayjs(dates.to_date, "YYYY-MM-DD HH:mm:ss"),
              ]
            : null
        }
        allowClear={true}
        disableFutureDates={true}
      />
    );
  }
);

DateRangeFilter.displayName = "DateRangeFilter";

export default DateRangeFilter;
