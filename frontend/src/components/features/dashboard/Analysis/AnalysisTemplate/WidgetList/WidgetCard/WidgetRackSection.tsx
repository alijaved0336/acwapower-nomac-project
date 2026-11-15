import React, { memo, useMemo } from "react";
import { AnalysisTemplateContext } from "../../../context/AnalysisTemplateContext";
import { useContextSelector } from "use-context-selector";
import ErrorState from "../../../../../../common/ErrorState";
import MultiSelect from "../../../../../../common/widgets/MultiSelect";
import { useGetAllRacksByTableAndSiteQuery } from "../../../../../../../store/api/analysisApi";
import { Widget } from "../../../../../../../types/analysis.types";

// Function to determine table type
function getTableType(tableName: string): "pump" | "rack" {
  // Regex to match any substring containing "pump" (case-insensitive)
  const pumpRegex = /pump/i;
  return pumpRegex.test(tableName) ? "pump" : "rack";
}

type WidgetRackSectionProps = {
  widget: Widget;
};

const WidgetRackSection: React.FC<WidgetRackSectionProps> = ({ widget }) => {
  // Get all widget tables (includes selectedTables + tables from all widgets)
  // This ensures rack options persist even when tables are unselected
  const allWidgetTables = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.allWidgetTables
  );

  // Get widget-specific rack selection from context
  const widgetSelectedRack = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.widgetSelectedRacks?.[widget.id] || null
  );

  const handleSelectWidgetRack = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSelectWidgetRack
  );

  // Extract unique table names from widget columns
  const widgetTableNames = useMemo(() => {
    if (!widget.columns || widget.columns.length === 0)
      return new Set<string>();

    return new Set(
      widget.columns
        .filter((col) => col && col.tableName)
        .map((col) => col.tableName)
    );
  }, [widget.columns]);

  // Determine table types from widget columns
  const tableTypes = useMemo(() => {
    if (widgetTableNames.size === 0)
      return { hasPump: false, hasRack: false, isMixed: false };

    const widgetColumns = (widget.columns || []).filter(
      (col) => col && col.tableName
    );
    const hasPump = widgetColumns.some(
      (col) => col.tableName && getTableType(col.tableName) === "pump"
    );
    const hasRack = widgetColumns.some(
      (col) => col.tableName && getTableType(col.tableName) === "rack"
    );

    return {
      hasPump,
      hasRack,
      isMixed: hasPump && hasRack,
    };
  }, [widget.columns, widgetTableNames.size]);

  // Use allWidgetTables instead of selectedTables to persist options
  // This ensures rack options remain available even when tables are unselected
  const { racks, isFetchingRacks, racksError } =
    useGetAllRacksByTableAndSiteQuery(allWidgetTables, {
      selectFromResult: ({ data, isLoading, isFetching, error }) => ({
        racks: data || [],
        isFetchingRacks: isLoading || isFetching,
        racksError: error,
      }),
      skip: allWidgetTables.length === 0,
    });

  // Filter racks to only show those matching widget's table type (pump or rack)
  const filteredRackOptions = useMemo(() => {
    if (!racks || !Array.isArray(racks) || widgetTableNames.size === 0)
      return [];

    // If widget has mixed table types, show all racks (both pump and rack)
    // Otherwise, filter by table type
    const filteredRacks = racks.filter((rack) => {
      if (!rack || !rack.tableName) return false;

      const rackTableType = getTableType(rack.tableName);

      if (tableTypes.isMixed) {
        // If widget has both pump and rack tables, show all racks
        return true;
      } else if (tableTypes.hasPump) {
        // If widget only has pump tables, show only pumps
        return rackTableType === "pump";
      } else if (tableTypes.hasRack) {
        // If widget only has rack tables, show only racks
        return rackTableType === "rack";
      }

      return false;
    });

    return filteredRacks
      .filter((rack) => rack && rack.rackValue)
      .map((rack) => ({
        label: rack.rackLabel || rack.rackValue,
        value: rack.rackValue,
      }));
  }, [racks, widgetTableNames, tableTypes]);

  // Determine placeholder text based on table types
  const placeholder = useMemo(() => {
    if (tableTypes.isMixed) {
      return "Select Rack/Pump";
    }
    return tableTypes.hasPump ? "Select Pump" : "Select Rack";
  }, [tableTypes]);

  // Ensure value is always an array and matches available options
  const selectedValue = useMemo(() => {
    if (!widgetSelectedRack) return [];
    const rackArray = Array.isArray(widgetSelectedRack)
      ? widgetSelectedRack
      : [widgetSelectedRack];

    // Filter to only include values that exist in filteredRackOptions
    const availableValues = new Set(
      filteredRackOptions.map((opt) => opt.value)
    );
    return rackArray.filter((val) => availableValues.has(val));
  }, [widgetSelectedRack, filteredRackOptions]);

  // Only show if widget has at least one column
  if (!widget.columns || widget.columns.length === 0) {
    return null;
  }

  if (racksError) {
    return <ErrorState className="h-[10vh]" />;
  }

  return (
    <>
      <style
        dangerouslySetInnerHTML={{
          __html: `
        .widget-rack-select-${widget.id} .ant-select-selector {
          overflow: hidden !important;
          height: auto !important;
          min-height: 32px !important;
        }
        .widget-rack-select-${widget.id} .ant-select-selection-overflow {
          overflow: hidden !important;
          flex-wrap: nowrap !important;
          display: flex !important;
          width: 100% !important;
        }
        .widget-rack-select-${widget.id} .ant-select-selection-overflow-item {
          flex-shrink: 1 !important;
          min-width: 0 !important;
          max-width: 100% !important;
        }
        .widget-rack-select-${widget.id} .ant-select-selection-item {
          max-width: 100% !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
          white-space: nowrap !important;
          display: inline-flex !important;
        }
        .widget-rack-select-${widget.id} .ant-select-selection-placeholder {
          white-space: nowrap !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
        }
        .widget-rack-select-${widget.id} .ant-select-selection-search {
          flex-shrink: 0 !important;
        }
      `,
        }}
      />
      <div
        style={{
          width: "180px",
          minWidth: "180px",
          maxWidth: "180px",
          flexShrink: 0,
        }}
      >
        <MultiSelect
          value={selectedValue}
          displayKey="label"
          valueKey="value"
          placeholder={placeholder}
          size="middle"
          maxTagCount={1}
          maxTagPlaceholder={(omitted) => `+${omitted.length} more`}
          style={{
            width: "100%",
          }}
          className={`widget-rack-select-${widget.id}`}
          options={filteredRackOptions}
          loading={isFetchingRacks}
          disabled={racksError || filteredRackOptions.length === 0}
          onChange={(value) =>
            handleSelectWidgetRack(
              widget.id,
              Array.isArray(value) ? value : null
            )
          }
        />
      </div>
    </>
  );
};

export default memo(WidgetRackSection);
