"use client";

import { Button, Flex, Typography, Grid } from "antd";
import React from "react";
import { sizeToken } from "../../../../styles/themes/tokens/size";
import Link from "next/link";
import { BackIcon } from "@/assets/icons";
import { colorToken } from "../../../../styles/themes/tokens/colors";
import { paddingToken } from "../../../../styles/themes/tokens/padding";
import Segmented from "@/components/common/widgets/Segmented";

const { useBreakpoint } = Grid;

const PlantHeader = () => {
  const size = useBreakpoint();
  const isMobile = size.xs;
  return (
    <Flex
      justify={"space-between"}
      align={"center"}
      wrap="wrap"
      gap={sizeToken.sizeMS}
      style={{
        backgroundColor: isMobile ? colorToken?.colorBgBase : "#f5faff",
        paddingInline: isMobile ? paddingToken.padding : 0,
        paddingBlock: isMobile ? paddingToken.paddingContentHorizontal : 0,
      }}
    >
      <Flex
        align={"center"}
        gap={sizeToken.sizeXS}
        style={{ width: isMobile ? "100%" : "auto" }}
      >
        <Link href={"/dashboard"}>
          <Button
            icon={<BackIcon width={7} height={14} />}
            type="text"
            style={{
              width: "28px",
              height: "28px",
              backgroundColor: "#EAECF0",
            }}
          />
        </Link>
        <Typography.Text
          style={{ fontSize: isMobile ? "20px" : "36px", fontWeight: 400 }}
        >
          Jubail 3A IWP
        </Typography.Text>
      </Flex>
      <Flex
        style={{
          width: isMobile ? "100%" : "auto",
          display: isMobile ? "block" : "flex",
        }}
      >
        <Segmented
          options={[
            {
              key: "OVERVIEW",
              value: "overview",
              label: "Overview",
            },
            {
              key: "SYNOPRIC",
              value: "synopric",
              label: "Synopric",
            },
          ]}
          onChange={(value) => {}}
          currentOption={{
            key: "OVERVIEW",
            value: "overview",
            label: "Overview",
          }}
          //   otherProps={{ block: !!isMobile }}
        />
      </Flex>
    </Flex>
  );
};

export default PlantHeader;
