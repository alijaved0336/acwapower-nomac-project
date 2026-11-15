"use client";

import React from "react";
import { Tabs } from "antd";
import { pumpIdTabsStyle } from "../utils/styles";
import { formatPumpName } from "../utils/chartHelpers";

interface PumpIdTabsProps {
  pumps: Array<{ pump: string; Pump_id: string }>;
  activeKey: string;
  onChange: (pumpId: string) => void;
}

const PumpIdTabs: React.FC<PumpIdTabsProps> = ({
  pumps,
  activeKey,
  onChange,
}) => {
  const items = pumps.map((pump) => {
    const pumpName = formatPumpName(pump.pump);
    return {
      key: pump.Pump_id,
      label: (
        <span style={{ fontSize: "13px" }}>
          {pumpName}{" "}
          <span style={{ fontSize: "0.75em", color: "#555" }}>
            (KKS: {pump.Pump_id})
          </span>
        </span>
      ),
    };
  });

  return (
    <Tabs
      activeKey={activeKey}
      onChange={onChange}
      items={items}
      style={{
        ...pumpIdTabsStyle,
        marginLeft: "16px",
      }}
      tabBarStyle={{
        marginBottom: 0,
      }}
      tabBarGutter={14}
    />
  );
};

export default PumpIdTabs;
