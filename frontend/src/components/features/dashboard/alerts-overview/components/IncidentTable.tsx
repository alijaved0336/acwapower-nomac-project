"use client";

import React, { useMemo, useState } from "react";
import Table from "../../../../common/Table";
import { cn } from "../../../../../utils";
import type { ColumnsType } from "antd/es/table";
import { useFormattedAntColumns } from "../../../../../utils/tableConfig";
import { Empty } from "antd";
import styles from "../styles/incidentTable.module.css";

const CompactFirstPassTable: React.FC = ({}) => {
  const fontSizeMultiplier = 1;
  const [page] = useState(1);
  const [limit] = useState(12);

  // Dummy data
  const allTableData = useMemo(
    () => [
      {
        key: "1",
        label: "Frequency",
        flat: "777 pm",
        over: "777 pm",
        l3: "777 pm",
        l4: "777 pm",
      },
      {
        key: "2",
        label: "Density",
        flat: "777 pm",
        over: "777 pm",
        l3: "777 pm",
        l4: "777 pm",
      },
      {
        key: "3",
        label: "Court",
        flat: "777 pm",
        over: "777 pm",
        l3: "777 pm",
        l4: "777 pm",
      },
    ],
    []
  );

  // Paginate data
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, limit]);

  // Dummy time
  const displayTime = useMemo(() => {
    return "12:30:45";
  }, []);

  const baseColumns = useMemo((): ColumnsType<any> => {
    return [
      {
        title: "",
        dataIndex: "label",
        key: "label",
        width: 120,
        render: (text: string) => (
          <strong
            style={{
              fontSize: `${12 * fontSizeMultiplier}px`,
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            {text}
          </strong>
        ),
      },
      {
        title: "Flat time",
        dataIndex: "flat",
        key: "flat",
        align: "center",
        render: (text: string) => (
          <span
            style={{
              fontSize: `${12 * fontSizeMultiplier}px`,
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            {text}
          </span>
        ),
      },
      {
        title: "Over limit",
        dataIndex: "over",
        key: "over",
        align: "center",
        render: (text: string) => (
          <span
            style={{
              fontSize: `${12 * fontSizeMultiplier}px`,
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            {text}
          </span>
        ),
      },
      {
        title: "Label 3",
        dataIndex: "l3",
        key: "l3",
        align: "center",
        render: (text: string) => (
          <span
            style={{
              fontSize: `${12 * fontSizeMultiplier}px`,
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            {text}
          </span>
        ),
      },
      {
        title: "Label 4",
        dataIndex: "l4",
        key: "l4",
        align: "center",
        render: (text: string) => (
          <span
            style={{
              fontSize: `${12 * fontSizeMultiplier}px`,
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            {text}
          </span>
        ),
      },
    ];
  }, [fontSizeMultiplier]);

  const formattedColumns = useFormattedAntColumns(baseColumns, {
    capitalize: true,
  });

  return (
    <div className={cn(styles.container)}>
      <div className={styles.contentContainer}>
        {/* Table Title */}
        <div className={styles.header}>
          <div className={styles.headerIndicator}>
            <span
              className={styles.title}
              style={{ fontSize: `${18 * fontSizeMultiplier}px` }}
            >
              Incident Overview
            </span>
          </div>
          {displayTime && (
            <span
              className={styles.timeBadge}
              style={{ fontSize: `${12 * fontSizeMultiplier}px` }}
            >
              Time: {displayTime}
            </span>
          )}
        </div>
        <div className={styles.tableContainer}>
          <style jsx global>{`
            .hide-scrollbar::-webkit-scrollbar {
              display: none; /* Chrome, Safari, Opera - hides both scrollbars */
            }
            .ant-table-sticky-scroll {
              display: none !important; /* Hide Ant Design's sticky scrollbar */
            }
            .ant-table-thead > tr > th {
              font-size: ${14 * fontSizeMultiplier}px !important;
              padding: 6px 6px !important;
              font-weight: 600 !important;
              height: auto !important;
              font-family:
                "Inter",
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                sans-serif !important;
              white-space: normal !important;
              word-wrap: break-word !important;
              line-height: 1.3 !important;
            }
            .ant-table-tbody > tr {
              height: auto !important;
            }
            .ant-table-tbody > tr > td {
              font-size: ${9 * fontSizeMultiplier}px !important;
              padding: 4px 6px !important;
              font-family:
                "Inter",
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                sans-serif !important;
            }
            .ant-table-thead > tr > th.datetime-column,
            .ant-table-tbody > tr > td.datetime-column {
              padding-left: 2px !important;
              padding-right: 2px !important;
            }

            /* Responsive: Reduce padding and font sizes at 900px and below */
            @media (max-height: 900px) {
              .ant-table-thead > tr > th {
                padding: 4px 4px !important;
                font-size: ${10 * fontSizeMultiplier}px !important;
              }
              .ant-table-tbody > tr > td {
                padding: 3px 4px !important;
                font-size: ${8 * fontSizeMultiplier}px !important;
              }
              .ant-table-thead > tr > th.datetime-column,
              .ant-table-tbody > tr > td.datetime-column {
                padding-left: 2px !important;
                padding-right: 2px !important;
              }
            }
          `}</style>
          <Table
            rowKey="key"
            data={tableData}
            columns={formattedColumns}
            pagination={false}
            size="small"
            borderRadius={0}
            loading={false}
            scroll={{ y: "calc(100% - 48px)" }}
            sticky={{ offsetHeader: 0 }}
            locale={{
              emptyText: (
                <div className={styles.emptyContainer}>
                  <Empty
                    description={
                      <span
                        className={styles.emptyText}
                        style={{ fontSize: `${11 * fontSizeMultiplier}px` }}
                      >
                        No Data
                      </span>
                    }
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                </div>
              ),
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default CompactFirstPassTable;
