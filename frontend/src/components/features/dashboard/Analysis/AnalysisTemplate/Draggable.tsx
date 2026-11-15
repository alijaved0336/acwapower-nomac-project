import React, { memo, PropsWithChildren } from "react";
import { useDraggable } from "@dnd-kit/core";
import { cn } from "../../../../../utils";

type DraggableProps = {
  id: string;
  data: any;
  className?: string;
} & PropsWithChildren;

function Draggable({ children, id, data, className }: DraggableProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id,
    data,
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={cn("cursor-grab", className)}
    >
      {children}
    </div>
  );
}

export default memo(Draggable);
