import { Card } from "antd";
import React, { FC } from "react";
import LiquidGuage from "../../../../common/charts/LiquidGuage";
import ChartSpinner from "../../../../common/ChartSpinner";

type TotalProductionProps = {
  value: number;
  loading?: boolean;
};

const TotalProduction: FC<TotalProductionProps> = ({ value, loading }) => {
  return (
    <Card
      styles={{
        body: { padding: "0.5rem", height: "100%" },
      }}
      className="relative"
    >
      {loading && <ChartSpinner />}

      <div className="h-full w-full">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 transition-colors dark:text-white">
          Total Production
        </h3>
        <LiquidGuage
          title="Total Water Usage"
          unit="MLDs"
          max={value}
          value={value}
        />
      </div>
    </Card>
  );
};

export default TotalProduction;
