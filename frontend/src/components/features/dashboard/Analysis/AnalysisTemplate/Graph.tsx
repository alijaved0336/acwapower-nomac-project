import React, { FC, memo } from "react";
import { ColumnData, WidgetType } from "../../../../../types/analysis.types";
import EChartsGraph from "./EChartsGraph";
import DynamicDataTable from "./DynamicDataTable";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";

type GraphProps = {
  widgetId: string;
  widgetType: WidgetType;
  columns: ColumnData[];
  yaxisOptions?: EChartsYAxisConfig[];
  heatmapConfig?: HeatmapConfig | null;
};

const Graph: FC<GraphProps> = ({
  widgetId,
  columns,
  widgetType,
  yaxisOptions,
  heatmapConfig,
}) => {
  if (widgetType === "table") {
    return <DynamicDataTable data={columns} />;
  }

  return (
    <EChartsGraph
      widgetId={widgetId}
      columns={columns}
      widgetType={widgetType}
      yaxisOptions={yaxisOptions}
      heatmapConfig={heatmapConfig}
    />
  );
};

export default memo(Graph);
