"use client";

import { Flex, Typography, theme } from "antd";
import { sizeToken } from "@/styles/themes/tokens/size";

import type { FC } from "react";
import { LightBulbIcon, WaterDropIcon } from "@/assets/icons";
import { formatNumber } from "@/utils/numberUtils";
import { getPlantName } from "../../Analysis/utils/utils";

interface IProps {
  plantType: string;
  production: number;
  sec: number;
  availability: number;
  quality: string;
  dailyDispatch: string;
  dailyDispatchPercentage: string;
  clusterName?: string;
}

const PlantCard: FC<IProps> = (props) => {
  const { token } = theme.useToken();

  const isWater = props.plantType === "WATER";
  const Icon = isWater ? WaterDropIcon : LightBulbIcon;

  // Helper function to format daily dispatch values
  const formatDailyDispatch = (value: string) => {
    if (!value || value === "N/A") {
      return "N/A";
    }

    // Remove % symbol and extract numeric value
    const cleanValue = value.replace(/%/g, "").trim();

    // Check if it's a valid number
    if (!isNaN(parseFloat(cleanValue))) {
      return formatNumber(parseFloat(cleanValue));
    }

    return cleanValue;
  };

  return (
    <Flex vertical gap={sizeToken.sizeXS} style={{ padding: "4px 0" }}>
      {/* Header with Plant Name and Cluster */}
      <Flex align="center" gap={sizeToken.sizeXS}>
        <Icon width={20} height={20} style={{ color: token.colorText }} />
        <Typography.Text
          strong
          style={{
            fontSize: "14px",
            fontWeight: 600,
            color: token.colorText,
          }}
        >
          {getPlantName(props.plantType)}
        </Typography.Text>
        <Typography.Text
          style={{
            fontSize: "11px",
            fontWeight: 400,
            color: token.colorTextTertiary,
            marginLeft: "4px",
          }}
        >
          {props.clusterName || "KSA"}
        </Typography.Text>
      </Flex>

      {/* Last Day MLDs Information */}
      <Typography.Text
        style={{
          fontSize: "12px",
          fontWeight: 400,
          color: token.colorTextSecondary,
          marginTop: "2px",
        }}
      >
        Last Day MLDs: {formatDailyDispatch(props.dailyDispatch)} MLD (
        {formatDailyDispatch(props.dailyDispatchPercentage)}%)
      </Typography.Text>
    </Flex>
  );
};

export default PlantCard;
