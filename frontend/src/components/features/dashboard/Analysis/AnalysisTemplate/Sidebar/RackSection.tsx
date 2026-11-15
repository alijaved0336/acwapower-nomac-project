import React, { memo, useMemo } from "react";

import { AnalysisTemplateContext } from "../../context/AnalysisTemplateContext";
import { useContextSelector } from "use-context-selector";
import ErrorState from "../../../../../common/ErrorState";
import MultiSelect from "../../../../../common/widgets/MultiSelect";
import { useGetAllRacksByTableAndSiteQuery } from "../../../../../../store/api/analysisApi";

const RacksList = () => {
  const selectedTables = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedTables
  );
  const { racks, isFetchingRacks, racksError } =
    useGetAllRacksByTableAndSiteQuery(selectedTables, {
      selectFromResult: ({ data, isLoading, isFetching, error }) => ({
        racks: data || [],
        isFetchingRacks: isLoading || isFetching,
        racksError: error,
      }),
      skip: selectedTables.length === 0,
    });
  const selectedRack = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedRack
  );
  const handleSelectRack = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSelectRack
  );

  const rackOptions = useMemo(() => {
    if (!racks || !Array.isArray(racks)) return [];

    return racks.map((rack) => ({
      label: rack.rackLabel || rack.rackValue,
      value: rack.rackValue,
    }));
  }, [racks]);

  if (racksError) {
    return <ErrorState className="h-[10vh]" />;
  }

  return (
    <MultiSelect
      value={selectedRack || []}
      displayKey="label"
      valueKey="value"
      placeholder="Select Rack"
      size="middle"
      maxTagCount={1}
      style={{ width: "100%", maxWidth: "220px" }}
      options={rackOptions}
      loading={isFetchingRacks}
      disabled={racksError}
      onChange={(value) =>
        handleSelectRack(Array.isArray(value) ? value : null)
      }
    />
  );
};

const RackSection = () => {
  return <RacksList />;
};

export default memo(RackSection);
