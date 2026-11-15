import type { ColumnsType } from "antd/es/table";
import { AnalysisTableRow } from "@/types/chemical.types";
import { theme } from "antd";

export const defaultTableScroll = {
  x: 1500,
  y: 400,
};

const formatDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;

    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return dateString;
  }
};

export const useGenerateAnalysisColumns = () => {
  const { token } = theme.useToken();

  return (tableData: AnalysisTableRow[]): ColumnsType<AnalysisTableRow> => {
    if (!tableData || tableData.length === 0) return [];

    const sampleRow = tableData[0];
    return Object.keys(sampleRow)
      .filter((key) => key !== "key")
      .map((key) => ({
        title: key,
        dataIndex: key,
        key: key,
        width:
          key.toLowerCase().includes("date") ||
          key.toLowerCase().includes("time")
            ? 180
            : 200,
        align: typeof sampleRow[key] === "number" ? "center" : "left",
        render: (value: any) => {
          if (
            value === null ||
            value === "No Data" ||
            (typeof value === "number" && isNaN(value))
          ) {
            return <span style={{ color: token.colorTextDisabled }}>-</span>;
          }

          if (typeof value === "number") {
            return (
              <span
                style={{
                  fontWeight: 500,
                  color:
                    value === 0 ? token.colorTextSecondary : token.colorPrimary,
                }}
              >
                {value.toFixed(3)}
              </span>
            );
          }

          if (
            key.toLowerCase().includes("date") ||
            key.toLowerCase().includes("time")
          ) {
            return (
              <span style={{ fontSize: "12px", color: token.colorText }}>
                {formatDateTime(value?.toString() || "")}
              </span>
            );
          }

          return value?.toString() || "-";
        },
      }));
  };
};

// Legacy export for backward compatibility
export const generateAnalysisColumns = (
  tableData: AnalysisTableRow[]
): ColumnsType<AnalysisTableRow> => {
  if (!tableData || tableData.length === 0) return [];

  const sampleRow = tableData[0];
  return Object.keys(sampleRow)
    .filter((key) => key !== "key")
    .map((key) => ({
      title: key,
      dataIndex: key,
      key: key,
      width:
        key.toLowerCase().includes("date") || key.toLowerCase().includes("time")
          ? 180
          : 200,
      align: typeof sampleRow[key] === "number" ? "center" : "left",
      render: (value: any) => {
        if (
          value === null ||
          value === "No Data" ||
          (typeof value === "number" && isNaN(value))
        ) {
          return <span style={{ color: "#999" }}>-</span>;
        }

        if (typeof value === "number") {
          return (
            <span
              style={{
                fontWeight: 500,
                color: value === 0 ? "#666" : "#1890ff",
              }}
            >
              {value.toFixed(3)}
            </span>
          );
        }

        if (
          key.toLowerCase().includes("date") ||
          key.toLowerCase().includes("time")
        ) {
          return (
            <span style={{ fontSize: "12px" }}>
              {formatDateTime(value?.toString() || "")}
            </span>
          );
        }

        return value?.toString() || "-";
      },
    }));
};

export const tableOtherProps = {
  scroll: defaultTableScroll,
  size: "small" as const,
};
