"use client";
import React, { FC } from "react";
import { Card, Skeleton } from "antd";
import { cn } from "../../../utils";

type SkeletonWidgetProps = {
  showControls?: boolean;
  isTable?: boolean;
  className?: string;
};

const SkeletonWidget: FC<SkeletonWidgetProps> = ({
  showControls = true,
  isTable = false,
  className,
}) => {
  return (
    <div className={cn("relative min-h-[50vh]", className)}>
      {showControls && (
        <div className="mb-3 flex justify-end gap-12">
          <Skeleton.Button
            style={{ minWidth: 32, width: "100%", height: 32 }}
          />
          <Skeleton.Button
            style={{ minWidth: 32, width: "100%", height: 32 }}
          />
          <Skeleton.Button
            style={{ minWidth: 32, width: "100%", height: 32 }}
          />
          <Skeleton.Button
            style={{ minWidth: 32, width: "100%", height: 32 }}
          />
        </div>
      )}
      {isTable && (
        <Skeleton.Input
          style={{
            height: "50px",
            width: "100%",
            borderTopLeftRadius: 8,
            borderTopRightRadius: 8,
            borderBottomLeftRadius: 0,
            borderBottomRightRadius: 0,
          }}
          className="border-b border-gray-200"
          block
        />
      )}

      <Skeleton.Input
        style={{
          height: isTable ? `calc(50vh - 50px)` : "50vh",
          width: "100%",
          borderTopLeftRadius: isTable ? 0 : 8,
          borderTopRightRadius: isTable ? 0 : 8,
          borderBottomLeftRadius: 8,
          borderBottomRightRadius: 8,
        }}
        active
        block
      />
    </div>
  );
};

export default SkeletonWidget;
