"use client";

import { Typography } from "antd";

import type { TPlantEquipmentKpi } from "@/types/plantEquipmentKpi.type";
import type { ColumnsType } from "antd/es/table";
import type { FC } from "react";
import Table from "../../../common/Table";
import { formatNumber, formatPercentage } from "@/utils/numberUtils";

const PlantEquipmentKpiTable: FC = () => {
  // Helper function to format equipment KPI values (without units)
  const formatEquipmentValue = (value: string, kpiName: string) => {
    if (!value || value === "") {
      return "N/A";
    }

    const kpiLower = kpiName.toLowerCase();

    // Handle string values that don't contain numeric data
    if (typeof value === "string" && !value.match(/\d/)) {
      return value; // Return as is for non-numeric strings
    }

    // Extract numeric value from strings like "77 %" or "777 m3/h"
    const numericMatch = value.match(/(\d+(?:\.\d+)?)/);
    if (!numericMatch) {
      return value; // Return as is if no numeric value found
    }

    const numericValue = parseFloat(numericMatch[1]);

    // Handle percentage values
    if (
      value.includes("%") ||
      kpiLower.includes("load") ||
      kpiLower.includes("availability")
    ) {
      return formatPercentage(numericValue);
    }

    // Handle numeric values (display without units since units are in separate column)
    return formatNumber(numericValue);
  };

  // Helper function to get units for equipment KPIs
  const getEquipmentKpiUnits = (kpiName: string) => {
    const kpiLower = kpiName.toLowerCase();

    if (kpiLower.includes("flow")) {
      return "m³/h";
    }
    if (kpiLower.includes("load") || kpiLower.includes("availability")) {
      return "%";
    }
    if (kpiLower.includes("sec")) {
      return "kWh/m³";
    }
    if (kpiLower.includes("power")) {
      return "kWh";
    }

    return "-";
  };

  const columns: ColumnsType<TPlantEquipmentKpi> = [
    {
      key: "kpi",
      dataIndex: "kpi",
      title: "KPI",
      render: (_, record) => (
        <Typography.Text strong>
          {record.kpi.toUpperCase() === "SEC" ? "SEC" : record.kpi}
        </Typography.Text>
      ),
    },
    {
      key: "intake",
      dataIndex: "intake",
      title: "Intake",
      render: (_, record) => formatEquipmentValue(record.intake, record.kpi),
    },
    {
      key: "pretreatment",
      dataIndex: "pretreatment",
      title: "Pretreatment",
      render: (_, record) =>
        formatEquipmentValue(record.pretreatment, record.kpi),
    },
    {
      key: "roHop",
      dataIndex: "roHop",
      title: "Ro-Hop",
      render: (_, record) => formatEquipmentValue(record.roHop, record.kpi),
    },
    {
      key: "roTrains",
      dataIndex: "roTrains",
      title: "Ro-Trains",
      render: (_, record) => formatEquipmentValue(record.roTrains, record.kpi),
    },
    {
      key: "ro2FeedPump",
      dataIndex: "ro2FeedPump",
      title: "Ro2-Feed Pump",
      render: (_, record) =>
        formatEquipmentValue(record.ro2FeedPump, record.kpi),
    },
    {
      key: "ro2Trains",
      dataIndex: "ro2Trains",
      title: "Ro2-Trains",
      render: (_, record) => formatEquipmentValue(record.ro2Trains, record.kpi),
    },
    {
      key: "postTreatment",
      dataIndex: "postTreatment",
      title: "Post Treatment",
      render: (_, record) =>
        formatEquipmentValue(record.postTreatment, record.kpi),
    },
    {
      key: "productWater",
      dataIndex: "productWater",
      title: "Product Water",
      render: (_, record) =>
        formatEquipmentValue(record.productWater, record.kpi),
    },
    {
      key: "units",
      dataIndex: "units",
      title: "Units",
      width: 80,
      render: (_, record) => (
        <Typography.Text
          style={{ color: "#666", fontSize: "14px", fontWeight: "bold" }}
        >
          {getEquipmentKpiUnits(record.kpi)}
        </Typography.Text>
      ),
    },
  ];

  return (
    <Table
      title="Plant Equipment KPIs"
      columns={columns}
      data={[
        {
          key: 1,
          kpi: "Flow",
          intake: "777 m3/h",
          pretreatment: "899 m3/h",
          roHop: "899 m3/h",
          roTrains: "999m3/h",
          ro2FeedPump: "899 m3/h",
          ro2Trains: "899 m3/h",
          postTreatment: "969 m3/h",
          productWater: "777 m3/h",
        },
        {
          key: 2,
          kpi: "Load",
          intake: "77 %",
          pretreatment: "97 %",
          roHop: "87.09 %",
          roTrains: "79 %",
          ro2FeedPump: "81 %",
          ro2Trains: "88 %",
          postTreatment: "54 %",
          productWater: "50 %",
        },
        {
          key: 3,
          kpi: "Sec",
          intake: "40 kw/m3",
          pretreatment: "54 kw/m3",
          roHop: "54 kw/m3",
          roTrains: "10 kw/m3",
          ro2FeedPump: "10 kw/m3",
          ro2Trains: "54 kw/m3",
          postTreatment: "5 kw/m3",
          productWater: "5 kw/m3",
        },
        {
          key: 4,
          kpi: "Power",
          intake: "543 kwh",
          pretreatment: "543 kwh",
          roHop: "543 kwh",
          roTrains: "543 kwh",
          ro2FeedPump: "54 kwh",
          ro2Trains: "643 kwh",
          postTreatment: "443 kwh",
          productWater: "443 kwh",
        },
        {
          key: 5,
          kpi: "Availability",
          intake: "80.5 %",
          pretreatment: "80.5 %",
          roHop: "60.5 %",
          roTrains: "54 %",
          ro2FeedPump: "80.5 %",
          ro2Trains: "95.4 %",
          postTreatment: "90.7 %",
          productWater: "90.7 %",
        },
      ]}
    />
  );
};

export default PlantEquipmentKpiTable;
