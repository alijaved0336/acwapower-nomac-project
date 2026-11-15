"use client";

import { Typography } from "antd";
import type { FC } from "react";

import Table from "@/components/common/Table";
import { Plant } from "../../../../types/energy.types";
import { formatNumber, formatPercentage } from "@/utils/numberUtils";
import { getKpiUnits, siteToKpiField } from "../Analysis/utils/utils";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";

type PlantKpiTableProps = {
  data: Array<Kpi>;
  selectedPlants?: Array<Plant>;
  selectedPlant?: string; // For specific plant selection
  loading?: boolean;
  cluster?: string;
};
type Kpi = {
  key: number;
  kpi: string;
  total: string;
  units?: string;
  [key: string]: any; // ✅ allow dynamic plant keys
};

const PlantKpiTable: FC<PlantKpiTableProps> = ({
  data,
  selectedPlants = [],
  selectedPlant,
  loading = false,
  cluster,
}) => {
  // Helper function to format KPI values based on their type (without units)
  const formatKpiValue = (value: any, kpiName: string) => {
    if (value === null || value === undefined || value === "") {
      return "N/A";
    }

    const kpiLower = kpiName.toLowerCase();

    // Handle special string values
    if (typeof value === "string") {
      // Handle "N/A" values
      if (value.toUpperCase() === "N/A") {
        return "N/A";
      }

      // Handle "None" values
      if (value.toUpperCase() === "NONE" || value.includes("None")) {
        return "None";
      }

      // Handle Quality KPI specifically - it comes as "OK%" from API
      if (kpiLower.includes("quality") && value.includes("OK")) {
        return "OK";
      }
    }

    // Extract numeric value from strings that might contain units
    let numericValue = value;
    if (typeof value === "string") {
      const numericMatch = value.match(/(\d+(?:\.\d+)?)/);
      if (numericMatch) {
        numericValue = parseFloat(numericMatch[1]);
      }
    }

    // Handle percentage values
    if (kpiLower.includes("availability")) {
      return formatPercentage(numericValue);
    }

    // Handle production values - append % to each value
    if (kpiLower.includes("production")) {
      if (
        typeof numericValue === "number" ||
        !isNaN(parseFloat(numericValue))
      ) {
        return `${formatNumber(numericValue)}`;
      }
    }

    // Handle numeric values (display without units since units are in separate column)
    if (typeof numericValue === "number" || !isNaN(parseFloat(numericValue))) {
      return formatNumber(numericValue);
    }

    // Return as is for non-numeric values
    return String(value);
  };

  // Transform plant-specific KPIs to the format expected by the table
  const transformPlantKpisToTableData = (plants: Plant[]): Kpi[] => {
    if (!plants || plants.length === 0) return [];

    // Get all unique KPI names from all plants
    const allKpiNames = new Set<string>();
    plants.forEach((plant) => {
      if (plant.plant_kpis) {
        plant.plant_kpis.forEach((kpi) => {
          allKpiNames.add(kpi.kpi);
        });
      }
    });

    // Create table data structure
    const tableData: Kpi[] = [];
    const kpiNames = Array.from(allKpiNames);

    kpiNames.forEach((kpiName, index) => {
      const kpiEntry: any = {
        key: index + 1,
        kpi: kpiName,
        total: "",
      };

      // Add plant-specific values
      plants.forEach((plant) => {
        const plantKpi = plant.plant_kpis?.find((kpi) => kpi.kpi === kpiName);
        if (plantKpi) {
          // Use plant name as key, fallback to site_name or id
          const plantKey = String(plant.name || plant.site_name || plant.id);

          // In the new format, the plant name is the key in the KPI object
          // For example: "Jubail Energy Plant": "25085.69921875 m3/h"
          const plantValue = plantKpi[plant.name] || plantKpi.total || "N/A";
          kpiEntry[plantKey] = String(plantValue);

          // Set total if available and not already set
          if (plantKpi.total && !kpiEntry.total) {
            kpiEntry.total = String(plantKpi.total);
          }
        }
      });

      tableData.push(kpiEntry);
    });

    return tableData;
  };

  // Determine which data format to use
  // If we have plants with plant_kpis (new format from cluster API), use that
  // Otherwise, use the original data format (from map-data API)
  const hasNewFormatData = selectedPlants.some(
    (plant) => plant.plant_kpis && plant.plant_kpis.length > 0
  );
  const tableData = hasNewFormatData
    ? transformPlantKpisToTableData(selectedPlants)
    : data;

  // Create a mapping of site names to KPI field names (case-insensitive)

  // Determine which columns to show based on selected plants
  const getVisibleColumns = () => {
    const baseColumns = [
      {
        key: "kpi",
        dataIndex: "kpi",
        title: "KPI",
        render: (_: any, record: Kpi) => (
          <Typography.Text strong>
            {record.kpi.toUpperCase() === "SEC" ? "SEC" : record.kpi}
          </Typography.Text>
        ),
      },
      {
        key: "units",
        dataIndex: "units",
        title: "Units",
        width: 90,
        render: (_: any, record: Kpi) => (
          <Typography.Text
            style={{ color: "#666", fontSize: "14px", fontWeight: "bold" }}
          >
            {getKpiUnits(record.kpi)}
          </Typography.Text>
        ),
      },
      {
        key: "total",
        dataIndex: "total",
        title: "Total",
        render: (_: any, record: Kpi) => (
          <Typography.Text strong style={{ color: "#1890ff" }}>
            {formatKpiValue(record.total, record.kpi)}
          </Typography.Text>
        ),
      },
    ];

    // If a specific plant is selected, show only that plant's column
    if (selectedPlant && selectedPlant !== "All Plants") {
      const matchingPlant = selectedPlants.find(
        (plant) =>
          plant.id === selectedPlant ||
          plant.name === selectedPlant ||
          plant.plant_type === selectedPlant ||
          plant.site_name === selectedPlant
      );

      if (matchingPlant) {
        // Check if we're using the new format
        const hasNewFormatData = selectedPlants.some(
          (plant) => plant.plant_kpis && plant.plant_kpis.length > 0
        );
        if (hasNewFormatData) {
          // New format: use plant name as key
          const plantKey = String(
            matchingPlant.name || matchingPlant.site_name || matchingPlant.id
          );

          baseColumns.push({
            key: plantKey,
            dataIndex: plantKey,
            title: getSiteDisplayName(
              matchingPlant.site_name || matchingPlant.name
            ),
            render: (_: any, record: Kpi) => (
              <Typography.Text>
                {formatKpiValue(record[plantKey as keyof Kpi], record.kpi)}
              </Typography.Text>
            ),
          });
        } else {
          // Old format: use the siteToKpiField mapping
          const siteName = (
            matchingPlant.site_name ||
            matchingPlant.name ||
            ""
          ).toLowerCase();
          const kpiField = siteToKpiField[siteName];
          if (kpiField && data.length > 0 && data[0][kpiField as keyof Kpi]) {
            baseColumns.push({
              key: kpiField,
              dataIndex: kpiField,
              title: getSiteDisplayName(
                matchingPlant.site_name || matchingPlant.name
              ),
              render: (_: any, record: Kpi) => (
                <Typography.Text>
                  {formatKpiValue(record[kpiField as keyof Kpi], record.kpi)}
                </Typography.Text>
              ),
            });
          }
        }
      }

      return baseColumns;
    }

    if (selectedPlants.length > 0) {
      selectedPlants.forEach((plant) => {
        // Use plant_type as it matches the data keys ("Jubail Energy Plant", etc.)
        let plantKey;
        if (cluster == "All Clusters") {
          plantKey = String(
            plant.plant_type || plant.name || plant.site_name || plant.id
          );
        } else {
          plantKey = getSiteDisplayName(
            String(
              plant.plant_type || plant.name || plant.site_name || plant.id
            )
          );
        }

        // Check if this plant key exists in the data
        if (
          tableData.length > 0 &&
          tableData[0][plantKey as keyof Kpi] !== undefined
        ) {
          baseColumns.push({
            key: plantKey,
            dataIndex: plantKey,
            title: getSiteDisplayName(
              plant.name || plant.site_name || plant.plant_type || ""
            ),
            render: (_: any, record: Kpi) => (
              <Typography.Text>
                {formatKpiValue(record[plantKey as keyof Kpi], record.kpi)}
              </Typography.Text>
            ),
          });
        }
      });

      return baseColumns;
    }

    // Add this condition BEFORE the "if (selectedPlant && selectedPlant !== "All Plants")" check

    // Case 3: Specific cluster selected + "All Plants" selected
    if (selectedPlant === "All Plants" && selectedPlants.length > 0) {
      console.log("Cluster Selected with All Plants:", cluster);
      selectedPlants.forEach((plant) => {
        // Use plant_type as the key since it matches the data structure
        const plantKey = String(plant.plant_type || plant.name);

        // Verify the key exists in the data
        if (
          tableData.length > 0 &&
          tableData[0][plantKey as keyof Kpi] !== undefined
        ) {
          baseColumns.push({
            key: plantKey,
            dataIndex: plantKey,
            title: getSiteDisplayName(
              plant.name || plant.site_name || plant.plant_type || ""
            ),
            render: (_: any, record: Kpi) => (
              <Typography.Text>
                {formatKpiValue(record[plantKey as keyof Kpi], record.kpi)}
              </Typography.Text>
            ),
          });
        }
      });

      return baseColumns;
    }

    // Default: show all columns
    const allColumns = [
      {
        key: "jazla",
        dataIndex: "Jubail Energy Plant",
        title: getSiteDisplayName("jazla"),
        render: (_: any, record: Kpi) => (
          <Typography.Text>
            {formatKpiValue(record["Jubail Energy Plant"], record.kpi)}
          </Typography.Text>
        ),
      },
      {
        key: "rabigh",
        dataIndex: "Rabigh Energy Plant",
        title: getSiteDisplayName("rabigh"),
        render: (_: any, record: Kpi) => (
          <Typography.Text>
            {formatKpiValue(record["Rabigh Energy Plant"], record.kpi)}
          </Typography.Text>
        ),
      },
      {
        key: "stpc",
        dataIndex: "STPC Energy Plant",
        title: getSiteDisplayName("stpc"),
        render: (_: any, record: Kpi) => (
          <Typography.Text>
            {formatKpiValue(record["STPC Energy Plant"], record.kpi)}
          </Typography.Text>
        ),
      },
      {
        key: "uaq",
        dataIndex: "UAQ Energy Plant",
        title: getSiteDisplayName("uaq"),
        render: (_: any, record: Kpi) => (
          <Typography.Text>
            {formatKpiValue(record["UAQ Energy Plant"], record.kpi)}
          </Typography.Text>
        ),
      },
    ];

    return [...baseColumns, ...allColumns];
  };

  const visibleColumns = getVisibleColumns();

  // Filter data to only show the required KPIs: Production, SEC, Power, and Quality
  const allowedKpis = ["production", "sec", "power", "quality"];
  const filteredData = tableData.filter((kpi) =>
    allowedKpis.some((allowedKpi) => kpi.kpi.toLowerCase().includes(allowedKpi))
  );

  return (
    <Table
      title=""
      rootClassName="h-[300px] overflow-y-auto shadow-2xl"
      columns={visibleColumns}
      data={filteredData}
      loading={loading}
    />
  );
};

export default PlantKpiTable;
