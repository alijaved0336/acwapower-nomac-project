"use client";

import { Flex, Typography } from "antd";
import SummaryCard from "@/components/common/SummaryCard";
import { formatNumber, formatPercentage } from "@/utils/numberUtils";

const metricValue = (params: {
  value: number;
  unit: string;
  percent: number;
}) => {
  return (
    <Flex align="center" gap={4} justify="center">
      <Typography.Title level={4}>
        {formatNumber(params.value)}
      </Typography.Title>
      <Typography.Text style={{ color: "#475467", fontSize: "14px" }}>
        {params.unit}
      </Typography.Text>
      <Typography.Text style={{ color: "#344054", fontSize: "18px" }}>
        ({formatPercentage(params.percent)})
      </Typography.Text>
    </Flex>
  );
};

export const PlantSummary = () => {
  return (
    <div className="mx-auto grid w-full grid-cols-[repeat(auto-fit,minmax(min(100%,448px),1fr))] gap-16">
      <SummaryCard
        metric1Name="Production"
        metric1Value={metricValue({ value: 100, unit: "m3/h", percent: 100 })}
        metric2Name="Quality"
        metric2Value={<Typography.Title level={3}>OK</Typography.Title>}
        last24HoursValue={20}
        last7DaysValue={30}
        last30DaysValue={50}
        barValue={50}
        barColor="#A6F4C5"
      />
      <SummaryCard
        metric1Name="SEC"
        metric1Value={metricValue({
          value: 100,
          unit: "kw/m3",
          percent: 100,
        })}
        metric2Name="Sub-Api"
        metric2Value={metricValue({
          value: 100,
          unit: "kw/m3",
          percent: 100,
        })}
        last24HoursValue={15}
        last7DaysValue={25}
        last30DaysValue={60}
        barValue={50}
        barColor="#FFFAEB"
      />
      <SummaryCard
        metric1Name="Quality"
        metric1Value={
          <Typography.Title level={3}>{formatPercentage(20)}</Typography.Title>
        }
        last24HoursValue={25}
        last7DaysValue={25}
        last30DaysValue={50}
        barValue={50}
        barColor="#A6F4C5"
      />
    </div>
  );
};

export default PlantSummary;
