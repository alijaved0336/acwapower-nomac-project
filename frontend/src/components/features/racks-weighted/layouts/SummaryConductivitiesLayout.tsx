"use client";
import React, { memo } from "react";
import { Card, Skeleton } from "antd";
import { useRacksWeightedContext } from "../context/RacksWeightedContext";
import FirstPassTable from "../components/tables/FirstPassTable";
import SecondPassTable from "../components/tables/SecondPassTable";
import FirstPassTimeSeries from "../components/charts/FirstPassTimeSeries";
import SecondPassTimeSeries from "../components/charts/SecondPassTimeSeries";
import ConductivitiesCharts from "../components/charts/ConductivitiesCharts";
import RackFilter from "../components/RackFilter";
import SkeletonWidget from "../../../common/loaders/SkeletonWidget";

const SummaryConductivitiesLayout: React.FC = memo(() => {
  const { isInitialLoading } = useRacksWeightedContext();

  return (
    <div>
      <div className="mb-4 flex items-center justify-between px-12 py-6">
        {isInitialLoading ? (
          <>
            <Skeleton.Input active style={{ width: 300, height: 28 }} />
            <Skeleton.Input active style={{ width: 200, height: 40 }} />
          </>
        ) : (
          <>
            <h2 className="mb-1 text-2xl font-bold text-black">
              Weighted Conductivity 1st & 2nd Pass
            </h2>
            <RackFilter />
          </>
        )}
      </div>

      {isInitialLoading ? (
        <div className="!space-y-24">
          <Card>
            <SkeletonWidget />
          </Card>
          <Card>
            <SkeletonWidget />
          </Card>
          <Card>
            <SkeletonWidget />
          </Card>
          <Card>
            <SkeletonWidget />
          </Card>
          <Card>
            <SkeletonWidget isTable showControls={false} />
          </Card>
          <Card>
            <SkeletonWidget isTable showControls={false} />
          </Card>
        </div>
      ) : (
        <div className="!space-y-24">
          <ConductivitiesCharts />
          <FirstPassTimeSeries />
          <SecondPassTimeSeries />
          <h2 className="mb-1 px-2 text-2xl font-bold text-black">
            Racks Weighted Conductivity
          </h2>
          <FirstPassTable />
          <SecondPassTable />
        </div>
      )}
    </div>
  );
});

SummaryConductivitiesLayout.displayName = "SummaryConductivitiesLayout";

export default SummaryConductivitiesLayout;
