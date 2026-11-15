import React, { FC } from "react";
import ProcessConditionTable from "./ProcessConditionTable";
import Spinner from "../../../../../common/Spinner";
import { usePlantOverviewContext } from "../../context/plantOverviewContext";

interface UnitInServiceProps {
  compact?: boolean;
  className?: string;
}
const UnitInServiceCard: FC<UnitInServiceProps> = ({
  compact = false,
  className,
}) => {
  const { processOverviewTable, processOverviewTableLoading } =
    usePlantOverviewContext();
  const unitsInService = processOverviewTable?.data?.units_in_service;

  return (
    <div
    // className={className}
    // style={{
    //   position: "relative",
    //   display: "flex",
    //   flexDirection: "column",
    //   height: "100%",
    //   minHeight: 0,
    // }}
    >
      {processOverviewTableLoading && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            maxHeight: "100%",
            justifyContent: "center",
            // backgroundColor: "rgba(255,255,255,0.4)",
            zIndex: 10,
            borderRadius: 8,
          }}
        >
          <Spinner />
        </div>
      )}

      {unitsInService ? (
        <div
        // style={{
        //   borderRadius: "12px",
        //   border: "1px solid #e5e7eb",
        //   boxShadow: "0 2px 4px rgba(0, 0, 0, 0.08)",
        //   backgroundColor: "#ffffff",
        //   flex: 1,
        //   display: "flex",
        //   flexDirection: "column",
        //   minHeight: 0,
        // }}
        >
          <ProcessConditionTable
            processData={{ "Units in Service": unitsInService }}
            showFullHeight
            compact={compact}
          />
        </div>
      ) : null}
    </div>
  );
};

export default UnitInServiceCard;
