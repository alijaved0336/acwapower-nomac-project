// GridScroller.tsx
import React, {
  forwardRef,
  useRef,
  useLayoutEffect,
  useState,
  useMemo,
} from "react";
import { Components, Virtuoso } from "react-virtuoso";
import { cn } from "../../../../../../utils";

const List = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} {...props} className={cn("space-y-3", className)}>
      {children}
    </div>
  )
);

List.displayName = "List";

// 👇 Define Item outside
const Item = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} {...props} className={cn("px-8", className)}>
      {children}
    </div>
  )
);

Item.displayName = "Item";

const customVirtuosoComponents = {
  List,
  Item,
};

type VirtualizedScrollerProps<T> = {
  totalCount: number;
  itemContent: (index: number, item: T) => React.ReactNode;
  data: Array<T>;
  className?: string;
  virtuosoComponents?: Components<any, any> | undefined;
};

export default function VirtualizedScroller<T>({
  totalCount,
  data,
  itemContent,
  className,
  virtuosoComponents,
}: VirtualizedScrollerProps<T>) {
  const [scrollContainer, setScrollContainer] = useState<HTMLElement>();
  const containerRef = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    if (containerRef.current) {
      setScrollContainer(containerRef.current);
    }
  }, []);

  const finalvirtuosoComponents = useMemo(() => {
    if (virtuosoComponents)
      return { ...customVirtuosoComponents, ...virtuosoComponents };
    return customVirtuosoComponents;
  }, [virtuosoComponents]);

  return (
    <div
      className={cn(
        "custom-scroller max-h-[25vh] min-h-[1vh] overflow-x-hidden overflow-y-auto",
        className
      )}
      ref={containerRef}
    >
      <Virtuoso
        style={{ minHeight: "100%" }}
        customScrollParent={scrollContainer}
        totalCount={totalCount}
        data={data}
        components={finalvirtuosoComponents}
        // className="overflow-x-hidden"
        itemContent={itemContent}
      />
    </div>
  );
}
