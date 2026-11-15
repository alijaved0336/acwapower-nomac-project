"use client";

import React from "react";
import { useDroppable } from "@dnd-kit/core";

export default function MapDroppable({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isOver, setNodeRef } = useDroppable({ id: "map-container" });

  const style = {
    width: "100%",
    height: "100%",
    position: "relative" as const,
    border: isOver ? "2px dashed #1e90ff" : "none", // visual cue
  };

  return (
    <div ref={setNodeRef} style={style}>
      {children}
    </div>
  );
}
