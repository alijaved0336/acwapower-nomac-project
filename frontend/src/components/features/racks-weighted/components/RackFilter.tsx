"use client";
import React, { useMemo } from "react";
import MultiSelect from "@/components/common/widgets/MultiSelect";
import { useRacksWeightedContext } from "../context/RacksWeightedContext";
import { Rack } from "../../../../types/analysis.types";

interface RackFilterProps {
  style?: React.CSSProperties;
}

const RackFilter: React.FC<RackFilterProps> = ({ style }) => {
  const {
    selectedRacks,
    racks,
    racksLoading,
    selectedFilters,
    handleSelectRack,
  } = useRacksWeightedContext();

  const rackOptions = useMemo(
    () =>
      (Array.isArray(racks) ? racks : []).map((rack: Rack) => ({
        id: rack.rackValue,
        name: rack.rackLabel,
      })),
    [racks]
  );

  return (
    <div style={{ minWidth: "150px", maxWidth: "150px", ...style }}>
      <MultiSelect
        placeholder="Select Racks"
        value={selectedRacks}
        maxTagCount={1}
        onChange={(value) =>
          handleSelectRack(Array.isArray(value) ? value : null)
        }
        options={rackOptions}
        displayKey="name"
        valueKey="id"
        loading={racksLoading}
        disabled={!selectedFilters.plant}
        popupRender={(menu) => <>{menu}</>}
      />
    </div>
  );
};

export default RackFilter;
