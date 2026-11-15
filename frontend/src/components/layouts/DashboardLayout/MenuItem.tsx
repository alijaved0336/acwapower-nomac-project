"use client";

import { useMemo } from "react";

import { Flex } from "antd";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { DashboardIcon, PlantIcon, ReportIcon, UserIcon } from "@/assets/icons";

import type { FC } from "react";
import { sizeToken } from "@/styles/themes/tokens/size";
import QueryStatsIcon from "@mui/icons-material/QueryStats";

interface IProps {
  label: string;
  href: string;
}

export const MenuItem: FC<IProps> = (props) => {
  const pathname = usePathname();
  const isActive = pathname === props.href;

  const logoColor = isActive ? "#005D99" : "black";

  const Icon = useMemo(() => {
    switch (props.href) {
      case "/dashboard":
        return <DashboardIcon width={15} height={15} stroke={logoColor} />;
      case "/plants":
        return (
          <PlantIcon
            width={15}
            height={15}
            stroke={logoColor}
            strokeWidth={1.5}
          />
        );
      case "/reports":
        return <ReportIcon width={15} height={15} stroke={logoColor} />;
      case "/userManagement":
        return <UserIcon width={15} height={15} stroke={logoColor} />;
      default:
        return <></>;
    }
  }, [props.href, logoColor]);

  return (
    <Flex
      align={"center"}
      style={{
        gap: sizeToken.sizeXS,
      }}
    >
      {Icon}
      <Link href={props.href}>{props.label}</Link>
    </Flex>
  );
};
