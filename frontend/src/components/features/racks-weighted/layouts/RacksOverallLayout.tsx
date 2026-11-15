"use client";
import React, { memo } from "react";
import { Card, Skeleton } from "antd";
import { useRacksWeightedContext } from "../context/RacksWeightedContext";
import OverallWeightedTable from "../components/tables/OverallWeightedTable";
import OverallWeightedChart from "../components/charts/OverallWeightedChart";
import SkeletonWidget from "../../../common/loaders/SkeletonWidget";
import Heading from "../../../common/typography/Heading";

const TableSkeletonLoader = () => (
  <div className="mb-6 overflow-hidden px-8">
    <div className="mb-4 grid grid-cols-5 gap-4 border-b pb-3">
      {[...Array(5)].map((_, i) => (
        <Skeleton.Input
          key={i}
          active
          size="small"
          block
          style={{ height: 24 }}
        />
      ))}
    </div>
    {[...Array(8)].map((_, rowIndex) => (
      <div key={rowIndex} className="mb-3 grid grid-cols-5 gap-4">
        {[...Array(5)].map((_, colIndex) => (
          <Skeleton.Input
            key={colIndex}
            active
            size="small"
            block
            style={{ height: 20 }}
          />
        ))}
      </div>
    ))}
  </div>
);

const ChartSkeletonLoader = () => (
  <div className="px-8">
    <Skeleton active paragraph={{ rows: 10 }} />
  </div>
);

const RacksOverallLayout: React.FC = memo(() => {
  const { isInitialLoading } = useRacksWeightedContext();

  return (
    <div className="space-y-16">
      <div>
        <div className="mb-4 flex items-center justify-between py-6">
          <Heading
            level={2}
            className="mb-1 px-2 text-2xl font-semibold text-black"
          >
            Overall Weighted Conductivity
          </Heading>
        </div>

        {isInitialLoading ? (
          <div className="!space-y-24">
            <SkeletonWidget showControls={false} isTable />
            <Card>
              <SkeletonWidget />
            </Card>
          </div>
        ) : (
          <div className="!space-y-24">
            <OverallWeightedTable />
            <OverallWeightedChart />
          </div>
        )}
      </div>
    </div>
  );
});

RacksOverallLayout.displayName = "RacksOverallLayout";

export default RacksOverallLayout;
