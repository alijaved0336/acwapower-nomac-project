"use client";

import { Button, theme } from "antd";
import React, { memo } from "react";
// import { ReloadOutlined } from "@ant-design/icons";
import DateRangePicker from "../../../../common/widgets/DateRangePicker";
// import RackSection from "./Sidebar/RackSection";
import dayjs from "dayjs";
import { DateFormat } from "../../../../../constants/enums";
import { AnalysisTemplateContext } from "../context/AnalysisTemplateContext";
import { useContextSelector } from "use-context-selector";

const AnalysisTemplateFilters = () => {
  const { token } = theme.useToken();

  const dateFilter = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.dateFilter
  );

  const isFetchingWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingWidgets
  );

  const handleResetFilters = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleResetFilters
  );

  const handleDatesChange = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleDatesChange
  );

  return (
    <div
      className="sticky top-[56px] z-10 mb-12 rounded-md p-12"
      style={{
        backgroundColor: token.colorBgContainer,
        border: `1px solid ${token.colorBorder}`,
        boxShadow: `0 2px 8px ${token.colorFillQuaternary}`,
      }}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left side - Label */}
        <div className="flex items-center gap-2">
          <span
            className="text-sm font-semibold"
            style={{ color: token.colorText }}
          >
            Filters
          </span>
        </div>

        {/* Right side - Filter controls */}
        <div className="flex basis-2/3 items-center gap-3">
          {/* Date Range Picker */}

          <DateRangePicker
            className="!w-full !grow"
            onChange={handleDatesChange}
            size="middle"
            disableFutureDates
            disabled={isFetchingWidgets}
            value={
              dateFilter
                ? [
                    dayjs(dateFilter.from_date, DateFormat.DATE_TIME_24H),
                    dayjs(dateFilter.to_date, DateFormat.DATE_TIME_24H),
                  ]
                : null
            }
            allowClear={false}
          />
          {/* Rack Dropdown Commmented out as we have added widget-specific selection*/}
          {/* <RackSection /> */}

          {/* Reset Button */}
          <Button onClick={handleResetFilters}>Reset Filters</Button>
        </div>
      </div>
    </div>
  );
};

export default memo(AnalysisTemplateFilters);
