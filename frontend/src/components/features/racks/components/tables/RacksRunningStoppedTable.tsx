"use client";
import React, { useMemo } from "react";
import Table from "@/components/common/Table";
import {
  filterStoppedRacks,
  generateRunningRacksColumns,
  defaultTableScroll,
} from "../../utils";
import { formatColumnTitle } from "../../../../../utils/tableConfig";
import { Empty } from "antd";

export type RackData = { rack: number; runTime: number; stopTime: number };

interface Props {
  rackData: RackData[];
  isLoading: boolean;
}

const RacksRunningTable: React.FC<Props> = ({ rackData, isLoading }) => {
  const running = useMemo(() => filterStoppedRacks(rackData), [rackData]);
  const columns = useMemo(() => {
    const baseColumns = generateRunningRacksColumns();
    return baseColumns.map((col) => ({
      ...col,
      title: formatColumnTitle(col.title),
    }));
  }, []);

  return (
    <Table
      rowKey={(row) => `rack-${row.rack}`}
      data={running}
      columns={columns}
      pagination={false}
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
            <Empty description="No Data" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        ),
      }}
      borderRadius={0}
      loading={isLoading}
    />
  );
};

export default RacksRunningTable;
