import React, { FC } from "react";
import { Flex } from "antd";
import { ApexSeriesData } from "../../ui";

type StackedProgressBarProps = {
  series: Array<ApexSeriesData>;
  color: string;
};

/**
 * A replacement for the ApexChart-based StackedProgressBar that avoids
 * dependencies on react-apexcharts while that library is missing.
 */
const StackedProgressBar: FC<StackedProgressBarProps> = ({ series, color }) => {
  // Calculate total to normalize if needed, though previously it assumed 0-100 scale
  return (
    <Flex
      style={{
        width: "100%",
        height: "53px",
        backgroundColor: "#f5f5f5",
        borderRadius: "6px",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {series.map((s, index) => {
        const value = typeof s.data[0] === "number" ? s.data[0] : 0;
        return (
          <div
            key={s.name || index}
            style={{
              height: "100%",
              width: `${value}%`,
              backgroundColor:
                index === 0
                  ? color
                  : `${color}${Math.max(20, 100 - index * 20).toString(16)}`,
              opacity: 1 - index * 0.2,
              transition: "width 0.3s ease",
            }}
            title={`${s.name}: ${value}%`}
          />
        );
      })}
    </Flex>
  );
};

export default StackedProgressBar;
