// utils/tableConfig.ts
import { useMemo } from "react";
import type {
  ColumnsType,
  ColumnType as AntColumnType,
  ColumnGroupType,
  TablePaginationConfig,
} from "antd/es/table";
import { ColumnData } from "@/types/analysis.types";
import { Input, Tag } from "antd";
import { useEffect, useState } from "react";

export function formatColumnTitle(
  title: string,
  capitalize: boolean = true
): string {
  const normalized = title.toLowerCase().trim();

  if (
    normalized.includes("datetime") ||
    normalized.includes("date time") ||
    normalized.includes("date_time") ||
    normalized.includes("Date_Time") ||
    normalized.includes("Date Time") ||
    normalized === "date" ||
    normalized === "time" ||
    normalized === "Date & Time" ||
    normalized === "date & time"
  ) {
    return "DateTime";
  }

  let formatted = title.replace(/_/g, " ");
  if (capitalize) {
    formatted = formatted.replace(/\b\w/g, (char) => char.toUpperCase());
  }
  return formatted;
}

/**
 * Formats Ant Design table columns by transforming titles
 * Handles nested column groups recursively
 */
export function useFormattedAntColumns<T extends object>(
  columns: ColumnsType<T>,
  options: { capitalize?: boolean } = { capitalize: true }
): ColumnsType<T> {
  return useMemo(() => {
    if (!Array.isArray(columns)) return [];

    const formatTitle = (title: string): string => {
      return formatColumnTitle(title, options.capitalize);
    };

    const deepFormat = (cols: ColumnsType<T>): ColumnsType<T> =>
      cols.map((col) => {
        const formattedTitle =
          typeof col.title === "string" ? formatTitle(col.title) : col.title;

        if ("children" in col && Array.isArray(col.children)) {
          const groupCol = col as ColumnGroupType<T>;
          return {
            ...groupCol,
            title: formattedTitle,
            children: deepFormat(groupCol.children),
          };
        }

        const normalCol = col as AntColumnType<T>;
        return {
          ...normalCol,
          title: formattedTitle,
        };
      });

    return deepFormat(columns);
  }, [columns, options.capitalize]);
}

// Common pagination configuration
export const usePaginationConfig = (
  page: number,
  limit: number,
  total: number,
  onPageChange: (newPage: number, newPageSize?: number) => void,
  showSizeChanger: boolean = true
) => {
  const maxPage = Math.max(1, Math.ceil(total / limit));
  const [inputValue, setInputValue] = useState(page.toString());

  // keep inputValue in sync when page changes externally
  useEffect(() => {
    setInputValue(page.toString());
  }, [page]);

  return {
    current: page,
    pageSize: limit,
    total,
    showSizeChanger: showSizeChanger,

    showTotal: (total: number, range: [number, number]) => {
      return (
        <div
          className="pagination-left"
          style={{ display: "flex", gap: 8, alignItems: "center" }}
        >
          <span style={{ fontWeight: "bold" }}>Go to Page</span>
          <Input
            aria-label="Go to page number"
            type="number"
            min={1}
            max={maxPage}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
            }}
            onPressEnter={(e) => {
              const raw = (e.target as HTMLInputElement).value.trim();
              if (!raw) return;

              let value = Number(raw);

              if (value < 1) value = 1;
              if (value > maxPage) value = maxPage;
              onPageChange(value, limit);
            }}
            style={{ width: "3rem" }}
            size="small"
          />
          <span className="total-text">Total {total} rows</span>
        </div>
      );
    },
    onChange: (newPage: number, newPageSize?: number) => {
      onPageChange(newPage, newPageSize);
    },
    onShowSizeChange: (current: number, size: number) => {
      onPageChange(1, size); // Reset to first page when page size changes
    },
    rootClassName: "!px-8",
  } as TablePaginationConfig;
};

export const generatePaginationConfig = usePaginationConfig;

// Global preferred order for columns
export const globalPreferredColumnOrder: string[] = [
  // IDs / Primary Keys first
  "Rack",
  "Train",
  "Train_Id",
  "rack",
  "train",
  "id",

  // Time / Date second
  "DateTime",
  "datetime",
  "timestamp",
  "Time",
  "Date",
  "Start",
  "Start_Time",
  "start_time",
  "End",
  "End_Time",
  "end_time",

  // Status / descriptors
  "Status",
  "Mode",
  "Activity",
  "Duration",
  "Duration_Hours",
];

/**
 * Global column sorting utility
 * Prioritizes Racks and DateTime fields according to global rules
 */
export const sortColumnsGlobally = <
  T extends { key?: React.Key; dataIndex?: any; title?: any },
>(
  columns: T[]
): T[] => {
  return [...columns].sort((a, b) => {
    // Helper to get string representation of column identifier
    const getName = (col: T) => {
      if (typeof col.title === "string") return col.title.toLowerCase();
      if (typeof col.dataIndex === "string") return col.dataIndex.toLowerCase();
      if (typeof col.key === "string") return col.key.toLowerCase();
      return "";
    };

    const nameA = getName(a);
    const nameB = getName(b);

    // Find index in preferred order
    // Use findIndex with flexible matching
    const indexA = globalPreferredColumnOrder.findIndex((key) => {
      const k = key.toLowerCase();
      return nameA === k || nameA.includes(k) || k.includes(nameA);
    });

    const indexB = globalPreferredColumnOrder.findIndex((key) => {
      const k = key.toLowerCase();
      return nameB === k || nameB.includes(k) || k.includes(nameB);
    });

    // If both are found in the preferred list, sort by index
    if (indexA !== -1 && indexB !== -1) {
      return indexA - indexB;
    }

    // If only one is found, prioritize it
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;

    // Default: existing order or alphabetical
    return 0; // Keep original order for unrelated columns
  });
};
