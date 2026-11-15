import { Flex, Progress, Typography } from "antd";

import { colorToken } from "@/styles/themes/tokens/colors";
import { fontToken } from "@/styles/themes/tokens/fonts";
import { paddingToken } from "@/styles/themes/tokens/padding";
import { sizeToken } from "@/styles/themes/tokens/size";

import type { FC, ReactNode } from "react";
import StackedProgressBar from "./charts/StackedProgressBar";
import { formatPercentage } from "@/utils/numberUtils";

interface IProps {
  metric1Name: string;
  metric1Value: ReactNode;
  metric2Name?: string;
  metric2Value?: ReactNode;
  last24HoursValue: number;
  last7DaysValue: number;
  last30DaysValue: number;
  barValue: number;
  barColor: string;
}

export const SummaryCard: FC<IProps> = (props) => {
  return (
    <Flex
      vertical
      justify="space-between"
      style={{
        height: "208px",
        // width: "100%",
        // maxWidth: "448px",
        borderRadius: sizeToken.sizeLG,
        border: `1px solid #F5F5F5`,
        backgroundColor: colorToken?.colorBgContainer,
        boxShadow: "0px 0px 4px 0px #1018281A",
        padding: paddingToken.paddingLG,
      }}
    >
      <Flex justify="space-between" align="center">
        <Typography.Text
          style={{ fontSize: "18px", fontWeight: 600, color: "#344054" }}
        >
          {props.metric1Name}
        </Typography.Text>
        {props.metric1Value}
      </Flex>
      {props.metric2Name && props.metric2Value && (
        <Flex justify="space-between" align="center">
          <Typography.Text
            style={{ fontSize: "18px", fontWeight: 600, color: "#344054" }}
          >
            {props.metric2Name}
          </Typography.Text>
          {props.metric2Value}
        </Flex>
      )}

      <Flex vertical gap={8}>
        <StackedProgressBar
          color={props.barColor}
          series={[
            { name: "Last 24 hrs", data: [props.last24HoursValue] },
            { name: "Last 7 days", data: [props.last7DaysValue] },
            { name: "Last 30 days", data: [props.last30DaysValue] },
          ]}
        />
        {/* <Progress
          percent={props.barValue}
          showInfo={false}
          strokeColor={props.barColor}
          size={{ height: 31 }}
        ></Progress> */}
        <Flex justify="space-between">
          <Flex vertical align="start">
            <Typography.Text style={{ fontSize: "14px", color: "#475467" }}>
              Last 24 hrs
            </Typography.Text>
            <Typography.Text
              style={{
                fontSize: fontToken?.fontSizeLG,
                fontWeight: 500,
                color: "#182230",
              }}
            >
              {formatPercentage(props.last24HoursValue)}
            </Typography.Text>
          </Flex>
          <Flex vertical align="center">
            <Typography.Text style={{ fontSize: "14px", color: "#475467" }}>
              Last 7 days
            </Typography.Text>
            <Typography.Text
              style={{
                fontSize: fontToken?.fontSizeLG,
                fontWeight: 500,
                color: "#182230",
              }}
            >
              {formatPercentage(props.last7DaysValue)}
            </Typography.Text>
          </Flex>
          <Flex vertical align="end">
            <Typography.Text style={{ fontSize: "14px", color: "#475467" }}>
              Last 30 days
            </Typography.Text>
            <Typography.Text
              style={{
                fontSize: fontToken?.fontSizeLG,
                fontWeight: 500,
                color: "#182230",
              }}
            >
              {formatPercentage(props.last30DaysValue)}
            </Typography.Text>
          </Flex>
        </Flex>
      </Flex>
    </Flex>
  );
};

export default SummaryCard;
