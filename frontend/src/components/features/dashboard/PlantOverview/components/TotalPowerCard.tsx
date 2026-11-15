import { Card } from "antd";
import React from "react";
import SpeedoMeterGuage from "../../../../common/charts/SpeedoMeterGuage";
import ChartSpinner from "../../../../common/ChartSpinner";

interface TotalPowerCardProps {
  value: number;
  unit?: string;
  min?: number;
  max?: number;
  loading?: boolean;
  title?: string;
  className?: string;
}

const TotalPowerCard = ({
  value,
  unit = "kWh",
  min = 0,
  max = 300,
  title = "Total Power",
  loading,
}: Readonly<TotalPowerCardProps>) => {
  return (
    <Card
      styles={{
        body: { padding: "0.5rem", height: "100%" },
      }}
      className="relative"
    >
      {loading && <ChartSpinner />}
      <h3 className="mb-4 text-lg font-semibold text-gray-900 transition-colors dark:text-white">
        Total Power
      </h3>

      <SpeedoMeterGuage
        value={value}
        min={min}
        max={max}
        title={title}
        unit={unit}
      />
    </Card>
  );
};

export default TotalPowerCard;
