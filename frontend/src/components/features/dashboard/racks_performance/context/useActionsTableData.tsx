import { useMemo } from "react";
import type { ColumnsType } from "antd/es/table";
import { getStatusBadgeStyle } from "../utils/pumpKPIsTableStyles";
import dayjs from "dayjs";
import { theme } from "antd";

interface ActionRecordDisplay {
  id: string;
  pumpName: string;
  action: string;
  dateTime: string;
  modified?: boolean;
  kks?: string | number;
}

export const useActionsTableData = (actionsData: any) => {
  const { token } = theme.useToken();

  return useMemo(() => {
    const tableData: ActionRecordDisplay[] = [];

    actionsData?.records?.forEach((record: any) => {
      if (record.statuses && Array.isArray(record.statuses)) {
        record.statuses.forEach((statusObj: any, index: number) => {
          tableData.push({
            id: `${record.pump}_${index}`,
            kks: record.Pump_ID,
            pumpName: record.pump,
            action: statusObj.status,
            dateTime: dayjs(statusObj.timestamp).format("DD-MM-YYYY HH:mm:ss"),
            modified: statusObj.modified === true,
          });
        });
      } else if (record.status) {
        tableData.push({
          id: `${record.pump}`,
          pumpName: record.pump,
          action: record.status,
          dateTime: dayjs(record.timestamp).format("DD-MM-YYYY HH:mm:ss"),
          modified: record.modified === true,
        });
      }
    });

    const columns: ColumnsType<ActionRecordDisplay> = [
      {
        title: "Pump Name",
        dataIndex: "pumpName",
        key: "pumpName",
        width: 200,
        render: (text: string, record) => (
          <span
            style={{
              fontWeight: 500,
              color: token.colorText,
            }}
          >
            {text}{" "}
            <span
              className="text-xs"
              style={{ color: token.colorTextTertiary }}
            >
              (KKS {record.kks})
            </span>
          </span>
        ),
      },
      {
        title: "Actions",
        dataIndex: "action",
        key: "action",
        width: 150,
        align: "left" as const,
        render: (action: string, record) => {
          if (!action)
            return (
              <span
                style={{
                  color: record.modified
                    ? token.colorTextTertiary
                    : token.colorTextTertiary,
                }}
              >
                N/A
              </span>
            );

          const style = record.modified
            ? {
                padding: "2px 6px",
                borderRadius: "4px",
                fontSize: "12px",
                fontWeight: 500,
                display: "inline-block",
                textAlign: "center" as const,
                minWidth: "56px",
                border: `1px solid ${token.colorBorder}`,
                backgroundColor: token.colorFillQuaternary,
                color: token.colorTextTertiary,
              }
            : getStatusBadgeStyle(action, false, token);

          return <span style={style}>{action}</span>;
        },
      },
      {
        title: "Date & Time",
        dataIndex: "dateTime",
        key: "dateTime",
        width: 200,
        align: "left" as const,
        render: (text: string, record) => (
          <span
            style={{
              color: record.modified
                ? token.colorTextTertiary
                : token.colorText,
            }}
          >
            {text}
          </span>
        ),
      },
    ];

    return { columns, tableData };
  }, [actionsData, token]);
};
