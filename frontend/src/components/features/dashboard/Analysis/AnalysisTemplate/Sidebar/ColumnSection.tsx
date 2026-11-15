import React, { memo, useMemo, useState } from "react";
import { Button, Collapse as AntCollapse, Tooltip } from "antd";

import { ChevronDownIcon, DotsGrid } from "../../../../../../assets/icons";

import { cn } from "../../../../../../utils";
import Draggable from "../Draggable";
import { AnalysisTemplateContext } from "../../context/AnalysisTemplateContext";
import SkeletonSection from "./SkeletonSection";

import Collapse from "./Collapse";
import { useContextSelector } from "use-context-selector";
import ErrorState from "../../../../../common/ErrorState";
import SearchInput from "../../../../../common/widgets/SearchInput";
import { useVirtualizer } from "@tanstack/react-virtual";
import { formatColumnTitle } from "@/utils/tableConfig";

const { Panel } = AntCollapse;

// eslint-disable-next-line react/display-name
const ColumnList = memo(({ searchQuery = "" }: { searchQuery: string }) => {
  const parentRef = React.useRef<HTMLDivElement>(null);

  const selectedTables = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedTables
  );

  const columns = useContextSelector(AnalysisTemplateContext, (v) => v.columns);

  const isFetchingColumns = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingColumns
  );

  const columnsError = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.columnsError
  );

  const filteredColumns = useMemo(() => {
    if (!columns || !Array.isArray(columns)) return [];

    // Apply normalization using tableConfig.ts function
    const formattedColumns = columns.map((col) => ({
      ...col,
      formattedName: formatColumnTitle(col.columnName, true),
    }));

    if (!searchQuery.trim()) return formattedColumns;

    const filtered = formattedColumns.filter(
      (col) =>
        col.formattedName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        col.tableName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        col.siteName.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (filtered.length === 0) {
      return [];
    }

    return filtered;
  }, [columns, searchQuery]);

  const rowVirtualizer = useVirtualizer({
    count: filteredColumns.length,
    getScrollElement: () => parentRef.current,
    getItemKey: (index: number) => {
      const column = filteredColumns[index];
      return `${column.siteName}/${column.tableName}/${column.columnName}`;
    },
    estimateSize: () => 34,
    overscan: 50,
  });

  if (columnsError) {
    return <ErrorState className="h-[10vh]" />;
  }

  if (isFetchingColumns) {
    return (
      <div className="space-y-3">
        <SkeletonSection />
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      style={{
        height: `calc(59vh)`,
        width: `100%`,
        overflowY: "auto",
      }}
      className="custom-scroller"
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const col = filteredColumns[virtualRow.index];
          const uniqueId = `${col.siteName}/${col.tableName}/${col.columnName}`;

          return (
            <div
              key={virtualRow.key}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div ref={rowVirtualizer.measureElement}>
                <Draggable id={uniqueId} data={{ data: col, type: "plotting" }}>
                  <div className="text-text-base">
                    <Tooltip
                      title={
                        <div className="flex flex-col gap-1">
                          <div>
                            <span className="font-semibold">Name:</span>{" "}
                            <span>{col.formattedName}</span>
                          </div>
                          <div>
                            <span className="font-semibold">Type:</span>{" "}
                            <span>{col.columnType}</span>
                          </div>
                          <div>
                            <span className="font-semibold">Table:</span>{" "}
                            <span>{col.tableName}</span>
                          </div>
                        </div>
                      }
                      placement="top"
                    >
                      <div className="flex items-center gap-8 truncate">
                        <DotsGrid />
                        <span className="grow truncate">
                          {col.formattedName}
                        </span>
                      </div>
                    </Tooltip>
                  </div>
                </Draggable>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

const ColumnSection = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeKeys, setActiveKeys] = useState(["Columns"]);

  return (
    <Collapse
      bordered={false}
      defaultActiveKey={["Columns"]}
      activeKey={activeKeys}
      onChange={(keys) => setActiveKeys(keys)}
      expandIconPosition="end"
      expandIcon={({ isActive }) => (
        <Button
          size="small"
          icon={
            <ChevronDownIcon
              className={cn("!transition-all !duration-300 !ease-in-out", {
                "-rotate-90": !isActive,
              })}
            />
          }
        />
      )}
      className={cn(
        "!bg-bg-container dark:!bg-bg-elevated rounded-md px-6 py-16",
        {
          grow: activeKeys.includes("Columns"), // ← Apply grow class
        }
      )}
    >
      <Panel
        header={<p className="text-sm font-semibold">Columns</p>}
        key="Columns"
      >
        <SearchInput
          onSearch={(value) => setSearchQuery(value)}
          className="mb-8"
        />
        <ColumnList searchQuery={searchQuery} />
      </Panel>
    </Collapse>
  );
};

export default memo(ColumnSection);
