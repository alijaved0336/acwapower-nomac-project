import React, { useState } from "react";
import {
  pumpTabContainerStyle,
  pumpTabInnerStyle,
  getPumpTabButtonStyle,
} from "../utils/styles";

interface PumpTab {
  key: string;
  label: string;
}

interface PumpTabsProps {
  activeTab: string;
  onChange: (tab: string) => void;
  tabs: PumpTab[];
}

const PumpTabs: React.FC<PumpTabsProps> = ({ activeTab, onChange, tabs }) => {
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);

  if (!tabs || tabs.length === 0) {
    return null;
  }

  return (
    <div style={pumpTabContainerStyle}>
      <div style={{ ...pumpTabInnerStyle, gap: "4px" }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            onMouseEnter={() => setHoveredTab(tab.key)}
            onMouseLeave={() => setHoveredTab(null)}
            style={{
              ...getPumpTabButtonStyle(
                activeTab === tab.key,
                hoveredTab === tab.key
              ),
              padding: "6px 10px",
              fontSize: "13px",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default PumpTabs;
