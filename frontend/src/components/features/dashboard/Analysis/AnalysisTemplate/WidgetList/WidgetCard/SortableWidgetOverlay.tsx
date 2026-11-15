"use client";
import Image from "next/image";
import WidgetCardHeader from "./WidgetCardHeader";
import DynamicDataTable from "../../DynamicDataTable";
import { Widget } from "@/types/analysis.types";
import { FC, memo } from "react";
import { Card } from "antd";

const SortableWidgetOverlay: FC<{
  widget: Widget;
}> = ({ widget }) => {
  return (
    <Card className="card">
      <WidgetCardHeader widget={widget} />
      {widget.type === "table" ? (
        <DynamicDataTable data={widget.columns} />
      ) : (
        <Image
          src={widget.snapshot ?? ""}
          width={480}
          height={782}
          className="block w-full"
          alt="snapshot"
        />
      )}
    </Card>
  );
};

export default memo(SortableWidgetOverlay);
