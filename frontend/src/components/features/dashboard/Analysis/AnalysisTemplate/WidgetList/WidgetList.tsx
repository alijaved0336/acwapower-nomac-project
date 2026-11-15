"use client";

import React, { memo } from "react";

import AnalysisTemplateSkeleton from "../AnalysisTemplateSkeleton";
import { AnalysisTemplateContext } from "../../context/AnalysisTemplateContext";

import { useContextSelector } from "use-context-selector";
import ErrorState from "@/components/common/ErrorState";
import { ErrorResponse } from "@/store/services/axiosBaseQuery";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { DragOverlay } from "@dnd-kit/core";
import { isEmpty } from "lodash";
import AddNewWidget from "../AddNewWidget";

import SortableWidgetOverlay from "./WidgetCard/SortableWidgetOverlay";

import WidgetCard from "./WidgetCard/WidgetCard";

const WidgetList = () => {
  const widgets = useContextSelector(AnalysisTemplateContext, (v) => v.widgets);

  const activeWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.activeWidget
  );

  const isFetchingWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingWidgets
  );

  const widgetsError = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.widgetsError
  );

  // Show skeleton loader when fetching widgets
  if (isFetchingWidgets) return <AnalysisTemplateSkeleton />;

  if (widgetsError) {
    const error = widgetsError as ErrorResponse;
    return (
      <ErrorState
        className="h-[400px]"
        message={error.status === 404 ? (error.data as string) : undefined}
      />
    );
  }

  if (widgets.length === 0) return <AddNewWidget />;

  return (
    <>
      <SortableContext
        items={widgets.map((w) => w.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          style={{
            height: "calc(100vh - 140px)",
            width: "100%",
            overflowY: "auto",
            paddingRight: "10px",
          }}
          className="custom-scroller"
        >
          {widgets.map((widget) => (
            <div className="mb-12" key={widget.id}>
              <WidgetCard widget={widget} />
            </div>
          ))}
        </div>
      </SortableContext>

      <DragOverlay>
        {!isEmpty(activeWidget) && (
          <SortableWidgetOverlay widget={activeWidget} />
        )}
      </DragOverlay>
    </>
  );
};

export default memo(WidgetList);
