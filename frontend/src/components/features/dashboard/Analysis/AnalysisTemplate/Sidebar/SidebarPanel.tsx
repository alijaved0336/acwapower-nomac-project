import React, { memo, useState } from "react";
import SiteSection from "./SiteSection";
import TableSection from "./TableSection";
import ColumnSection from "./ColumnSection";
import { DragOverlay } from "@dnd-kit/core";
import { DotsGrid } from "../../../../../../assets/icons";
import { useContextSelector } from "use-context-selector";
import { AnalysisTemplateContext } from "../../context/AnalysisTemplateContext";

export const AssetDrawer = () => {
  const activeItem = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.activeItem
  );

  return (
    <>
      <div className="sticky top-[64px] flex h-[calc(100vh-64px)] w-[350px] flex-col !gap-8 overflow-y-hidden">
        {/* <div className="!space-y-8"> */}
        <SiteSection />
        <TableSection />
        <ColumnSection />
        {/* </div> */}
      </div>
      {activeItem && (
        <DragOverlay>
          <div className="text-text-base">
            <div className="flex items-center gap-8 truncate">
              <DotsGrid />
              <span className="grow truncate">{activeItem.columnName}</span>
            </div>
          </div>
        </DragOverlay>
      )}
    </>
  );
};

export default memo(AssetDrawer);
