import React, { FC } from "react";
import { Button, Collapse } from "antd";

import { DragOutlined } from "@ant-design/icons";
import { ChevronDownIcon, DotsGrid } from "../../../../../../assets/icons";
const { Panel } = Collapse;

import { cn } from "../../../../../../utils";

type CollapsibleSectionProps = {
  title: string;
  data: Array<string>;
  isDraggable?: boolean;
};

const CollapsibleSection: FC<CollapsibleSectionProps> = ({
  title,
  data,
  isDraggable = false,
}) => {
  return (
    <Collapse
      bordered={false}
      expandIconPosition="end"
      expandIcon={({ isActive }) => (
        <Button
          size="small"
          icon={
            <ChevronDownIcon
              className={cn("!transition-all !duration-300 !ease-in-out", {
                "-rotate-90": !isActive,
              })}
            />
          }
        />
      )}
      className="!bg-bg-container !rounded-md !p-8"
    >
      <Panel
        header={<p className="text-sm font-semibold">{title}</p>}
        key={title}
      >
        <div className="grid grid-cols-2 gap-3">
          {data?.map((item) => (
            <div
              key={item}
              className="text-text-disabled flex items-center gap-2"
            >
              <div className="flex items-center gap-12">
                <DotsGrid />
                <span>{item}</span>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </Collapse>
  );
};

export default CollapsibleSection;
