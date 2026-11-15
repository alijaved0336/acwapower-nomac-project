"use client";

import { DatePicker, theme } from "antd";
import React, { memo } from "react";
import { usePumpPerformance } from "../../context/PumpPerformanceContext";
import { formatString } from "../../../../../../utils/helpers";

const dateFormat = "YYYY-MM-DD HH:mm";

const PumpPerformanceFilters: React.FC<{ selectedPump?: string }> = ({
  selectedPump,
}) => {
  const { token } = theme.useToken();
  const { selectedDate, setSelectedDate, kpisLoading } = usePumpPerformance();

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
        {/* Left side - Pump Title */}
        <div className="flex items-center gap-2">
          <span
            className="text-sm font-semibold"
            style={{ color: token.colorText }}
          >
            {formatString(selectedPump ?? "") || "Pump KPIs"}
          </span>
        </div>

        {/* Right side - DatePicker */}
        <div className="flex items-center gap-3">
          <DatePicker
            value={selectedDate}
            onChange={(date) => setSelectedDate(date)}
            size="middle"
            format={dateFormat}
            showTime={{ format: "HH:mm" }}
            disabledDate={(current) =>
              current && current.isAfter(new Date(), "day")
            }
            disabled={kpisLoading}
            style={{ width: 200 }}
          />
        </div>
      </div>
    </div>
  );
};

export default memo(PumpPerformanceFilters);
