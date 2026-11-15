import React, {
  FC,
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
} from "react";
import WidgetCard from "./WidgetCard/WidgetCard";
import { Widget } from "../../../../../../types/analysis.types";
import { useVirtualizer } from "@tanstack/react-virtual";

type VirtualizedWidgetsProps = {
  widgets: Widget[];
};

type VirtualRowProps = {
  widget: Widget;
  index: number;
  measureRef: (el: HTMLElement | null) => void;
};

// eslint-disable-next-line react/display-name
const VirtualRow = forwardRef<HTMLDivElement, VirtualRowProps>(
  ({ widget, index, measureRef }, ref) => (
    <div
      data-index={index}
      ref={(el) => {
        measureRef(el);
        if (ref && typeof ref === "function") ref(el);
        else if (ref && "current" in ref) ref.current = el;
      }}
    >
      <div style={{ paddingBottom: "16px" }}>
        <WidgetCard widget={widget} />
      </div>
    </div>
  )
);

const VirtualizedWidgets: FC<VirtualizedWidgetsProps> = ({ widgets }) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

  const widgetIds = useMemo(
    () => widgets.map((w) => w.id).join(","),
    [widgets]
  );

  const virtualizer = useVirtualizer({
    count: widgets.length,
    getItemKey: (index: number) => widgets[index].id,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 400,
    overscan: 15,
  });

  const items = virtualizer.getVirtualItems();

  const measureRef = useCallback(
    (el: HTMLElement | null) => {
      if (!el) return;

      // 🔒 Guard: only measure elements that belong to virtual rows
      if (!el.hasAttribute("data-index")) return;

      virtualizer.measureElement(el);
    },
    [virtualizer]
  );

  const height = useMemo(() => virtualizer.getTotalSize(), [virtualizer]);

  return (
    <div
      ref={parentRef}
      style={{
        height: "calc(100vh - 140px)",
        width: "100%",
        contain: "strict",
        overflowY: "auto",
        paddingRight: "10px",
      }}
      className="custom-scroller"
    >
      <div
        style={{
          height: `${height}px`,
          width: "100%",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            transform: `translateY(${items[0]?.start ?? 0}px)`,
          }}
        >
          {items.map((virtualRow) => (
            <VirtualRow
              key={virtualRow.key}
              widget={widgets[virtualRow.index]}
              index={virtualRow.index}
              measureRef={measureRef}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default memo(VirtualizedWidgets);
