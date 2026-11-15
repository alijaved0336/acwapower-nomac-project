"use client";

import React, {
  FC,
  memo,
  useEffect,
  useMemo,
  useState,
  useTransition,
} from "react";
import { useDroppable } from "@dnd-kit/core";
import { Widget } from "@/types/analysis.types";

import { useContextSelector } from "use-context-selector";
import Spinner from "@/components/common/Spinner";

import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";
import { useYAxisConfigurator } from "../../../../../../../hooks/useYAxisConfigurator";
import YAxisConfiguratorModal from "../../../../../../common/modals/YAxisConfiguratorModal";
import CopyModal from "../../Sidebar/CopyModal";
import { cn } from "../../../../../../../utils";
import Graph from "../../Graph";
import { AnalysisTemplateContext } from "../../../context/AnalysisTemplateContext";
import WidgetCardHeader from "./WidgetCardHeader";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card, theme } from "antd";
import ChartSpinner from "../../../../../../common/ChartSpinner";

type WidgetCardPropTypes = {
  widget: Widget;
};

const WidgetCard: FC<WidgetCardPropTypes> = ({ widget }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [copyModalOpen, setCopyModalOpen] = useState(false);
  const [heatmapConfig, setHeatmapConfig] = useState<HeatmapConfig | null>(
    null
  );

  const [isPending, startTransition] = useTransition();

  const handleRemoveWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleRemoveWidget
  );

  const handleChangeWidgetName = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleChangeWidgetName
  );

  const handleClickWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleClickWidget
  );

  const handleSetYaxisOptions = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSetYaxisOptions
  );

  const handleRemoveColumnFromWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleRemoveColumnFromWidget
  );

  const widgetLoading = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.widgetLoading
  );

  const isFiltering = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFiltering
  );

  const isPendingDrop = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isPendingDrop
  );

  const { isOver, active, setNodeRef } = useDroppable({
    id: widget.id,
  });

  const {
    setNodeRef: setSortableNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging,
    isSorting,
  } = useSortable({ id: widget.id, data: { type: "sorting", widget } });

  useEffect(() => {
    if (!isDragging) return;
    document.body.style.cursor = "grabbing";
    return () => {
      document.body.style.cursor = "";
    };
  }, [isDragging]);

  const style = useMemo<React.CSSProperties>(() => {
    const transformValue = CSS.Transform.toString(transform);

    return {
      transform: transformValue,
      transition,
      zIndex: isDragging ? 999 : undefined,
      opacity: isDragging ? 0 : 1,
      pointerEvents: isDragging ? "none" : "auto",
    };
  }, [transform, transition, isDragging]);

  const type = active?.data?.current?.type;

  const isUpdating =
    widgetLoading[widget.id] || isPendingDrop || isFiltering || isPending;

  // Format column names before using them anywhere

  // Use formatted columns for all further processing
  const { numericColumns, ranges } = useYAxisConfigurator(widget.columns);

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    if (widget.type === "heatmap") {
      startTransition(() => {
        setHeatmapConfig(config as HeatmapConfig);
      });
    } else {
      startTransition(() => {
        handleSetYaxisOptions(widget.id, config as EChartsYAxisConfig[]);
      });
    }
    setModalOpen(false);
  };

  return (
    <Card
      ref={setSortableNodeRef}
      style={style}
      className={cn(
        "tw-rounded-lg tw-shadow-sm tw-bg-white tw-p-3 tw-mb-2 tw-transition-all card !overflow-hidden",
        {
          "tw-scale-[1.03] tw-shadow-lg": isDragging,
          "tw-opacity-80": isSorting,
          "tw-cursor-grabbing": isDragging,
        }
      )}
    >
      {modalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={widget?.yAxisOptions}
          numericColumns={numericColumns}
          ranges={ranges}
          open={modalOpen}
          columns={widget.columns} // from API
          chartType={widget.type} // Pass chart type
          widgetId={widget.id}
          onCancel={() => setModalOpen(false)}
          onSave={handleSave}
          onRemoveColumn={handleRemoveColumnFromWidget}
        />
      )}

      {copyModalOpen && (
        <CopyModal
          open={copyModalOpen}
          widgetId={widget.id}
          onCancel={() => setCopyModalOpen(false)}
          onSuccess={() => setCopyModalOpen(false)}
        />
      )}
      <div
        className={cn("relative min-h-[36vh]", {
          "opacity-50": isUpdating,
        })}
      >
        <div>
          {isUpdating && <ChartSpinner />}

          <WidgetCardHeader
            widget={widget}
            onChangeWidgetName={handleChangeWidgetName}
            onClickWidget={handleClickWidget}
            onRemoveWidget={handleRemoveWidget}
            onOpenYaxisModal={() => setModalOpen(true)}
            onOpenCopyWidgetModal={() => setCopyModalOpen(true)}
            dragHandleProps={{ ...attributes, ...listeners }}
          />
          <div
            ref={setNodeRef}
            className={cn("mt-8", {
              "outline-primary pointer-events-none rounded-lg outline-2 outline-offset-4":
                isOver && type !== "sorting",
            })}
          >
            <Graph
              widgetId={widget.id}
              widgetType={widget.type}
              columns={widget.columns}
              yaxisOptions={widget?.yAxisOptions}
              heatmapConfig={heatmapConfig}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};

export default memo(WidgetCard);
