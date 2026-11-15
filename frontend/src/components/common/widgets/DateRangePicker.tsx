import React, { FC, useEffect, useRef, useState } from "react";
import { DatePicker, TimePicker, Button, Typography, Divider } from "antd";
import type { RangePickerProps } from "antd/es/date-picker";
import dayjs, { Dayjs } from "dayjs";
import { DateFormat, TimeFormat } from "../../../constants/enums";
import { CalendarOutlined, ClockCircleOutlined } from "@ant-design/icons";
import { DateRangePickerType } from "../../../types/common.types";

const disableFutureDatesState = (current: dayjs.Dayjs) => {
  return current && current > dayjs().endOf("day");
};

const { RangePicker } = DatePicker;
const { Text } = Typography;

const presets = [
  { label: "Last 7 Days", days: 7 },
  { label: "Last 14 Days", days: 14 },
  { label: "Last 30 Days", days: 30 },
  { label: "Last Quarter", days: 90 },
  { label: "Last 6 Months", days: 180 },
  { label: "Last Year", days: 365 },
];

type DateRangePickerProps = {
  timeFormat?: TimeFormat;
  dateFormat?: DateFormat;
  disableFutureDates?: boolean;
  showTime?: boolean;
  size?: "small" | "middle" | "large";
  value?: DateRangePickerType;
  onChange?: (dates: DateRangePickerType) => void;
  defaultStartTime?: string;
  defaultEndTime?: string;
} & RangePickerProps;

const DateRangePicker: FC<DateRangePickerProps> = ({
  dateFormat = DateFormat.DATE_TIME_24H,
  timeFormat = TimeFormat.TIME_24H,
  disableFutureDates,
  showTime = true,
  value,
  onChange,
  size = "middle",
  ...rest
}) => {
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [startTime, setStartTime] = useState(dayjs().startOf("day"));
  const [endTime, setEndTime] = useState(dayjs().endOf("day"));
  const isDateSelected = useRef(false);

  // Determine the actual date format to use
  const effectiveDateFormat = showTime ? dateFormat : "YYYY-MM-DD";

  const handleSave = () => {
    if (range && range[0] && range[1]) {
      let mergedDates: [Dayjs, Dayjs];

      if (showTime) {
        // Merge date and time together
        mergedDates = [
          range[0]
            .hour(startTime.hour())
            .minute(startTime.minute())
            .second(startTime.second()),
          range[1]
            .hour(endTime.hour())
            .minute(endTime.minute())
            .second(endTime.second()),
        ];
      } else {
        // Use start of day for start date and end of day for end date
        mergedDates = [range[0].startOf("day"), range[1].endOf("day")];
      }

      // Call parent onChange with merged dates
      if (onChange) {
        onChange(mergedDates);
      }
    }

    setPickerOpen(false);
  };

  const handlePresetClick = (days: number) => {
    const start = dayjs().subtract(days, "days").startOf("day");
    const end = dayjs().endOf("day");

    setRange([start, end]);
  };

  // Combine date and time for display
  const getDisplayValue = (): [Dayjs, Dayjs] | null => {
    if (!range || !range[0] || !range[1]) return null;

    if (showTime) {
      return [
        range[0]
          .hour(startTime.hour())
          .minute(startTime.minute())
          .second(startTime.second()),
        range[1]
          .hour(endTime.hour())
          .minute(endTime.minute())
          .second(endTime.second()),
      ];
    }

    return range;
  };

  useEffect(() => {
    if (value && value[0] && value[1]) {
      setRange([value[0], value[1]]);

      if (showTime) {
        setStartTime(
          dayjs()
            .hour(value[0].hour())
            .minute(value[0].minute())
            .second(value[0].second())
        );
        setEndTime(
          dayjs()
            .hour(value[1].hour())
            .minute(value[1].minute())
            .second(value[1].second())
        );
      }
    } else {
      setRange(null);
      setStartTime(dayjs().startOf("day"));
      setEndTime(dayjs().endOf("day"));
    }
  }, [value, showTime]);

  return (
    <RangePicker
      {...rest}
      size={size}
      open={pickerOpen}
      value={getDisplayValue()}
      onChange={(dates) => {
        if (dates) {
          isDateSelected.current = true;
          setRange([dates[0]!, dates[1]!]);
        } else {
          setRange(null);
          setStartTime(dayjs().startOf("day"));
          setEndTime(dayjs().endOf("day"));
        }
      }}
      onCalendarChange={(dates) => {
        if (dates) {
          if (dates[0] && dates[1]) {
            setRange([dates[0], dates[1]]);
          }
        }
      }}
      onOpenChange={(open) => {
        setTimeout(() => {
          if (open) {
            setPickerOpen(open);
          } else if (!isDateSelected.current) {
            setPickerOpen(open);
          }
          isDateSelected.current = false;
        }, 100);
      }}
      getPopupContainer={(trigger) =>
        document.querySelector<HTMLElement>(".content-area-main") ||
        document.body
      }
      format={effectiveDateFormat}
      disabledDate={disableFutureDates ? disableFutureDatesState : undefined}
      showTime={false}
      suffixIcon={<CalendarOutlined className="text-slate-400" />}
      panelRender={(panelNode) => (
        <div
          className="flex items-start rounded-xl shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Custom Header with Presets */}
          <div className="max-h-[630px] overflow-y-auto px-16 py-8">
            <div className="flex flex-1 flex-col items-center justify-center gap-3">
              {presets.map((preset) => (
                <Button
                  key={preset.days}
                  variant="outlined"
                  onClick={() => handlePresetClick(preset.days)}
                  className="w-[130px] justify-center text-center font-medium"
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Calendar Panel */}
          <div className="border-l-border-secondary border-l-1">
            <div className="p-2">{panelNode}</div>

            {/* Time Selection Footer - Only show if showTime is true */}
            {showTime && (
              <div className="border-t border-slate-200 px-16 py-5">
                <div className="mb-2">
                  <div className="mb-8 flex items-center gap-2">
                    <Text className="text-sm font-bold text-slate-800">
                      Time Range
                    </Text>
                  </div>
                  <div className="grid grid-cols-2 gap-16">
                    {/* Start Time */}
                    <div className="rounded-lg border border-slate-200 p-8 shadow-sm">
                      <div className="mb-8 flex items-center gap-4">
                        <ClockCircleOutlined className="text-sm text-blue-600" />
                        <Text className="text-xs font-semibold text-slate-600">
                          Start Time
                        </Text>
                      </div>
                      <TimePicker
                        value={startTime}
                        onChange={(time) => time && setStartTime(time)}
                        format={timeFormat}
                        className="w-full rounded-lg"
                        placeholder="00:00:00"
                        size={size}
                      />
                    </div>

                    {/* End Time */}
                    <div className="rounded-lg border border-slate-200 p-8 shadow-sm">
                      <div className="mb-8 flex items-center gap-4">
                        <ClockCircleOutlined className="text-sm text-indigo-600" />
                        <Text className="text-xs font-semibold text-slate-600">
                          End Time
                        </Text>
                      </div>
                      <TimePicker
                        value={endTime}
                        onChange={(time) => time && setEndTime(time)}
                        format={timeFormat}
                        className="w-full rounded-lg"
                        placeholder="23:59:59"
                        size={size}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div
              className={`flex justify-end gap-3 border-t border-slate-200 px-16 py-5`}
            >
              <Button
                size="middle"
                className="rounded-lg px-6 font-medium"
                onClick={() => setPickerOpen(false)}
              >
                Cancel
              </Button>
              <Button
                size="middle"
                type="primary"
                className="rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-8 font-medium shadow-lg hover:from-blue-700 hover:to-indigo-700"
                onClick={handleSave}
              >
                Apply
              </Button>
            </div>
          </div>
        </div>
      )}
    />
  );
};

export default DateRangePicker;
