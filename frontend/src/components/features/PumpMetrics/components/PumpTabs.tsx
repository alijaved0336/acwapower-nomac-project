import { useMemo, useState } from "react";
import {
  pumpTabsContainerStyle,
  tabsWrapperStyle,
  getTabButtonStyle,
  getTabHoverStyle,
  getTabLeaveStyle,
} from "../utils/pumpTabStyles";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import { Tabs } from "antd";
import { formatColumnTitle } from "../../../../utils/tableConfig";

export function PumpTabs() {
  const { pumpsData, activeGroup, activePump, setActiveGroup, setActivePump } =
    usePumpMetricsContext();
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const mainGroups = useMemo(() => Object.keys(pumpsData || {}), [pumpsData]);

  return (
    <>
      {/* Group Tabs */}
      <div style={pumpTabsContainerStyle}>
        <div style={tabsWrapperStyle}>
          {mainGroups.map((group, index) => {
            const isActive = activeGroup === group;
            const isFirst = index === 0;
            const isLast = index === mainGroups.length - 1;
            const isHovered = hoveredTab === group;

            return (
              <button
                key={group}
                onClick={() => {
                  setActiveGroup(group);
                  const firstPump = pumpsData?.[group]?.[0] || null;
                  if (firstPump) setActivePump(firstPump);
                }}
                onMouseEnter={() => setHoveredTab(group)}
                onMouseLeave={() => setHoveredTab(null)}
                style={{
                  ...getTabButtonStyle(isActive, isFirst, isLast),
                  ...(isHovered
                    ? getTabHoverStyle(isActive)
                    : getTabLeaveStyle(isActive)),
                }}
              >
                {formatColumnTitle(
                  group
                    .split("_")
                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(" ")
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Pump Tabs */}
      {activeGroup && Array.isArray(pumpsData?.[activeGroup]) && (
        <Tabs
          activeKey={activePump?.Pump_id || ""}
          onChange={(pumpId) => {
            const found = pumpsData?.[activeGroup]?.find(
              (p) => p.Pump_id === pumpId
            );
            if (found) setActivePump(found);
          }}
          items={pumpsData[activeGroup].map((p) => ({
            key: p.Pump_id,
            label: (
              <span>
                {formatColumnTitle(p.pump)}{" "}
                <span style={{ color: "#999" }}>({p.Pump_id})</span>
              </span>
            ),
          }))}
          className="custom-pump-tabs"
          tabBarStyle={{ gap: "12px", padding: "0 10px" }}
        />
      )}
    </>
  );
}
