"use client";
import { useDndMonitor } from "@dnd-kit/core";

type DisableEchartsPointerEventsOnDragProps = {
  onDragOver: (acitveId: string, overId: string) => void;
};

function DisableEchartsPointerEventsOnDrag({
  onDragOver,
}: DisableEchartsPointerEventsOnDragProps) {
  useDndMonitor({
    onDragStart() {
      if (typeof document !== "undefined") {
        document
          .querySelectorAll(".echarts, .echarts-for-react")
          .forEach((el) => {
            (el as HTMLElement).style.pointerEvents = "none";
          });
      }
    },
    onDragEnd() {
      if (typeof document !== "undefined") {
        document
          .querySelectorAll(".echarts, .echarts-for-react")
          .forEach((el) => {
            (el as HTMLElement).style.pointerEvents = "auto";
          });
      }
    },
    onDragCancel() {
      if (typeof document !== "undefined") {
        document
          .querySelectorAll(".echarts, .echarts-for-react")
          .forEach((el) => {
            (el as HTMLElement).style.pointerEvents = "auto";
          });
      }
    },
    onDragOver(event) {
      const { active, over } = event;

      if (
        active?.data?.current?.type === "sorting" &&
        over?.data?.current?.type === "sorting"
      ) {
        onDragOver(active?.id as string, over?.data?.current?.widget?.id);
      }
    },
  });

  return null; // no UI, just a side-effect
}

export default DisableEchartsPointerEventsOnDrag;
