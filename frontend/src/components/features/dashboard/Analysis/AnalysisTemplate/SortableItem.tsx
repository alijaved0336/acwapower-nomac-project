"use client";
import React, { FC, memo, useEffect, useMemo } from "react";
import { CSS } from "@dnd-kit/utilities";
import { useSortable } from "@dnd-kit/sortable";
import classNames from "classnames";
import { Widget } from "../../../../../types/analysis.types";
import { Card, Tooltip } from "antd";
import { HolderOutlined } from "@ant-design/icons";

type SortableItemProps = {
  widget: Widget;
  children: React.ReactNode;
  dragOverlay?: boolean; // overlay-mode (used inside <DragOverlay>)
};

const SortableItem: FC<SortableItemProps> = ({
  widget,
  children,
  dragOverlay,
}) => {
  const {
    setNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging,
    isSorting,
  } = useSortable({ id: widget.id, data: { type: "sorting", widget } });

  // 👇 Cursor side effect
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
      transform: dragOverlay ? undefined : transformValue,
      transition,
      zIndex: isDragging ? 999 : undefined,
      opacity: isDragging && !dragOverlay ? 0 : 1,
      pointerEvents: isDragging && !dragOverlay ? "none" : "auto",
    };
  }, [transform, transition, isDragging, dragOverlay]);

  return (
    <div
      ref={setNodeRef}
      style={style}
      // {...(!dragOverlay ? { ...attributes, ...listeners } : {})}
      className={classNames(
        "tw-rounded-lg tw-shadow-sm tw-bg-white tw-p-3 tw-mb-2 tw-transition-all",
        {
          "tw-scale-[1.03] tw-shadow-lg": isDragging && dragOverlay,
          "tw-opacity-80": isSorting,
          "tw-cursor-grabbing": isDragging,
        }
      )}
    >
      {/* Drag handle in top-right */}

      <Card
        title={
          <div className="mb-2 flex justify-end">
            <span
              {...attributes}
              {...listeners}
              className="cursor-grab text-gray-500 hover:text-gray-700"
            >
              <Tooltip title="Drag to reorder" placement="top">
                <HolderOutlined />
              </Tooltip>
            </span>
          </div>
        }
      >
        {children}
      </Card>
    </div>
  );
};

export default memo(SortableItem);

// 👇 Overlay-only: doesn’t need widget or drag states
