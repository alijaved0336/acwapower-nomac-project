"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { useMap } from "react-leaflet";
import { FullViewIcon, MinusIcon, PlusIcon } from "@/assets/icons";
import { FC, useEffect } from "react";
import { theme } from "antd";

type DraggableZoomControlProps = {
  position: { x: number; y: number };
  bounds?: L.LatLngBoundsExpression;
};

const DraggableZoomControl: FC<DraggableZoomControlProps> = ({
  position,
  bounds,
}) => {
  const map = useMap();
  const { token } = theme.useToken();

  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: "zoom-control",
    });

  // Disable map dragging when component is being dragged
  useEffect(() => {
    if (isDragging) {
      map.dragging.disable();
    } else {
      map.dragging.enable();
    }
  }, [isDragging, map]);

  const containerStyle: React.CSSProperties = {
    position: "absolute",
    top: `${position.y}px`,
    left: `${position.x}px`,
    zIndex: 1000,
    width: "50px",
    borderRadius: "6px",
    backgroundColor: token.colorBgElevated,
    padding: "6px",
    boxShadow: isDragging
      ? `0 25px 50px -12px rgba(0, 0, 0, 0.25)`
      : `0 4px 12px rgba(0, 0, 0, 0.15)`,
    transform: isDragging
      ? `${CSS.Translate.toString(transform)} scale(1.05)`
      : CSS.Translate.toString(transform),
    transition: isDragging
      ? "none"
      : "box-shadow 0.2s ease, transform 0.2s ease",
    border: `1px solid ${token.colorBorder}`,
  };

  const handleFullView = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (bounds) {
      map.fitBounds(bounds, { padding: [20, 20], duration: 0.5 });
    } else {
      map.fitBounds(map.getBounds(), { padding: [20, 20], duration: 0.5 });
    }
  };

  const handleZoomIn = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    map.zoomIn();
  };

  const handleZoomOut = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    map.zoomOut();
  };

  const buttonStyle: React.CSSProperties = {
    display: "flex",
    width: "100%",
    cursor: "pointer",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "4px",
    padding: "8px",
    backgroundColor: "transparent",
    border: "none",
    color: token.colorText,
    transition: "background-color 0.2s",
  };

  // Icon color - white in dark mode for contrast
  const iconColor = token.colorText;

  return (
    <div ref={setNodeRef} {...listeners} {...attributes} style={containerStyle}>
      {/* Control buttons */}
      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {/* Zoom In */}
        <div
          style={{
            borderRadius: "4px",
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            paddingBottom: "2px",
          }}
        >
          <button
            draggable={false}
            onClick={handleZoomIn}
            style={buttonStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = token.colorFillSecondary;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
          >
            <PlusIcon
              style={{
                height: "16px",
                width: "16px",
              }}
              color={iconColor}
            />
          </button>
        </div>

        {/* Zoom Out */}
        <div style={{ borderRadius: "4px" }}>
          <button
            draggable={false}
            onClick={handleZoomOut}
            style={buttonStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = token.colorFillSecondary;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
          >
            <MinusIcon
              style={{
                height: "16px",
                width: "16px",
              }}
              color={iconColor}
            />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DraggableZoomControl;
