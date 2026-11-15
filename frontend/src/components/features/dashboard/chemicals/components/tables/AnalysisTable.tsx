"use client";
import React, { useState, useEffect, useMemo, memo, useRef } from "react";
import Table from "@/components/common/Table";
import Spinner from "@/components/common/Spinner";
import { cn } from "@/utils";
import { useChemicalDataContext } from "../../context/ChemicalDataContext";
import {
  generateAnalysisColumns,
  tableOtherProps,
} from "../../utils/TableConfig";
import { useFormattedAntColumns } from "../../../../../../utils/tableConfig";
import { generatePaginationConfig } from "@/utils/tableConfig";
import { Card, Empty, Button, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "../../../../../../utils/chartExport";

interface AnalysisTableProps {
  selectedChemical?: string;
  selectedArea?: string;
  selectedSiteName?: string;
  dates?: { from_date: string | null; to_date: string | null } | null;
}

const AnalysisTable: React.FC<AnalysisTableProps> = memo((props) => {
  const {
    tableData,
    isGlobalLoading,
    error,
    data_availability_for_given_date,
    from_date,
    to_date,
  } = useChemicalDataContext();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(5);
  const isFirstLoad = useRef(true);

  const apiConfigs = useMemo(
    () => [
      {
        key: "chemical",
        name: "Chemical Analysis",
        data_availability_for_given_date: data_availability_for_given_date,
        from_date: from_date,
        to_date: to_date,
        isLoading: isGlobalLoading,
        isFetching: isGlobalLoading,
      },
    ],
    [data_availability_for_given_date, from_date, to_date, isGlobalLoading]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  useEffect(() => {
    setPage(1);
  }, [
    props.selectedChemical,
    props.selectedArea,
    props.selectedSiteName,
    props.dates,
  ]);

  useEffect(() => {
    if (!isGlobalLoading) {
      isFirstLoad.current = false;
    }
  }, [isGlobalLoading]);

  const columns = useMemo(
    () => generateAnalysisColumns(tableData),
    [tableData]
  );

  const showSpinner = isGlobalLoading && !isFirstLoad.current;

  const formattedColumns = useFormattedAntColumns(columns, {
    capitalize: true,
  });

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!tableData || tableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const chemicalName = props.selectedChemical
      ? props.selectedChemical.replace(/_/g, "_")
      : "chemical_analysis";
    const filename = getFilenameFromTitle(chemicalName);

    if (format === "csv") {
      exportTableToCSV(tableData, formattedColumns as any, filename);
    } else {
      exportTableToExcel(tableData, formattedColumns as any, filename);
    }
  };

  const downloadMenuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Download as CSV",
      onClick: () => handleDownload("csv"),
      disabled: !tableData || tableData.length === 0,
    },
    {
      key: "excel",
      label: "Download as Excel",
      onClick: () => handleDownload("excel"),
      disabled: !tableData || tableData.length === 0,
    },
  ];

  const moreMenuItems: MenuProps["items"] = [
    {
      key: "download",
      type: "submenu",
      label: "Download",
      children: downloadMenuItems,
    },
  ];

  return (
    <Card>
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-800">
          {props.selectedChemical
            ? props.selectedChemical.replace(/_/g, " ")
            : "Chemical Analysis"}{" "}
        </h2>
        {/* 3-Dots Menu */}
        <Dropdown menu={{ items: moreMenuItems }} trigger={["click"]}>
          <Button
            icon={<MoreOutlined />}
            size="small"
            style={{ height: "24px" }}
          />
        </Dropdown>
      </div>

      {/* Table Section */}

      <Table
        rowKey="key"
        data={error ? [] : tableData}
        columns={formattedColumns}
        pagination={generatePaginationConfig(
          page,
          limit,
          tableData.length,
          (newPage, newPageSize) => {
            setPage(newPage);
            if (newPageSize) setLimit(newPageSize);
          }
        )}
        borderRadius={0}
        loading={showSpinner}
        scroll={{ y: "calc(50vh - 82px)", x: undefined }}
        locale={{
          emptyText: (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "calc(50vh - 115px)",
                width: "100%",
              }}
            >
              <Empty
                description="No Data"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            </div>
          ),
        }}
      />

      {error && (
        <div className="flex h-32 items-center justify-center">
          <p className="font-medium text-red-500">
            Failed to load chemical data
          </p>
        </div>
      )}
    </Card>
  );
});

AnalysisTable.displayName = "AnalysisTable";

export default AnalysisTable;
