"use client";

import React from "react";
import { theme } from "antd";
import { usePlantOverviewContext } from "../../context/plantOverviewContext";
import ProcessConditionTable from "./ProcessConditionTable";
import Spinner from "../../../../../common/Spinner";

interface ProcessConditionCardProps {
  compact?: boolean;
  showFullHeight?: boolean;
  className?: string;
}

const ProcessConditionCard: React.FC<ProcessConditionCardProps> = ({
  compact = false,
  showFullHeight = false,
  className,
}) => {
  const { token } = theme.useToken();

  const { processOverviewTable, processOverviewTableLoading } =
    usePlantOverviewContext();

  const processCondition = processOverviewTable?.data?.process_condition;

  return (
    <div>
      {processOverviewTableLoading && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            maxHeight: "100%",
            justifyContent: "center",
            backgroundColor: token.colorBgMask,
            zIndex: 10,
            borderRadius: 8,
          }}
        >
          <Spinner />
        </div>
      )}
      <ProcessConditionTable
        processData={processCondition}
        tableTitle="Process Condition"
        showFullHeight={showFullHeight}
        compact={compact}
      />
    </div>
  );
};

export default ProcessConditionCard;
