"use client";

import React, { FC, useMemo } from "react";
import type { ColumnsType } from "antd/es/table";
import Table from "../../../../common/Table";

type DataTableProps = {
  data: Array<any>;
};

// Define a type for your dummy rows
interface DummyRow {
  key: string;
  column1: string;
  column2: string;
  column3: string;
  column4: string;
}

// Dummy columns
const dummyColumns: ColumnsType<DummyRow> = [
  {
    title: "Column 1",
    dataIndex: "column1",
    key: "column1",
  },
  {
    title: "Column 2",
    dataIndex: "column2",
    key: "column2",
  },
  {
    title: "Column 3",
    dataIndex: "column3",
    key: "column3",
  },
  {
    title: "Column 4",
    dataIndex: "column4",
    key: "column4",
  },
];

// Dummy data
const dummyData: DummyRow[] = [
  {
    key: "1",
    column1: "Value 1-1",
    column2: "Value 1-2",
    column3: "Value 1-3",
    column4: "Value 1-4",
  },
  {
    key: "2",
    column1: "Value 2-1",
    column2: "Value 2-2",
    column3: "Value 2-3",
    column4: "Value 2-4",
  },
  {
    key: "3",
    column1: "Value 3-1",
    column2: "Value 3-2",
    column3: "Value 3-3",
    column4: "Value 3-4",
  },
];

const DataTable: FC<DataTableProps> = ({ data }) => {
  const columns = useMemo(() => {
    return Array.isArray(data) && data.length > 0
      ? [
          { title: "KPI", dataIndex: "kpi", key: "kpi" },
          { title: "Jazla", dataIndex: "jazla", key: "jazla" },
          { title: "Rabigh", dataIndex: "rabigh", key: "rabigh" },
          { title: "STPC", dataIndex: "stpc", key: "stpc" },
          { title: "UAQ", dataIndex: "uaq", key: "uaq" },
        ]
      : dummyColumns;
  }, [data]);

  const tableData = Array.isArray(data) && data.length > 0 ? data : dummyData;

  return <Table title="Analysis Data" columns={columns} data={tableData} />;
};

export default DataTable;
