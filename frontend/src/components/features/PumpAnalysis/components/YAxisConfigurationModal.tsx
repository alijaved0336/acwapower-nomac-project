import React, { useEffect, useState } from "react";
import {
  Modal,
  InputNumber,
  Select,
  Radio,
  Button,
  RadioChangeEvent,
} from "antd";
import chroma from "chroma-js";

export interface SingleYAxisConfig {
  min?: number;
  max?: number;
  color?: string;
  position?: "left" | "right";
}

export interface YAxisConfig {
  [id: string]: SingleYAxisConfig;
}

export interface MetricConfig {
  id: string; // Unique identifier (e.g., 'yAxis1', 'yAxis2')
  label: string; // Display name (e.g., 'Head Measured')
}

// Color options matching the reference modal
const baseColors = [
  "#e6194b", // red
  "#3cb44b", // green
  "#ffe119", // yellow
  "#4363d8", // blue
  "#f58231", // orange
  "#911eb4", // purple
  "#46f0f0", // cyan
  "#f032e6", // magenta
  "#bcf60c", // lime
  "#fabebe", // light pink
  "#00ced1", // dark turquoise
  "#9a6324", // brown
  "#800000", // maroon
  "#808000", // olive
  "#000075", // navy
  "#aaffc3", // mint
];

const darkColors = baseColors.map((c) => chroma(c).darken(2).hex());

const COLOR_OPTIONS = darkColors.map((c, i) => ({
  value: c,
  label: (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span
        style={{
          display: "inline-block",
          width: 16,
          height: 16,
          backgroundColor: c,
          borderRadius: 4,
        }}
      />
      {c.toUpperCase()}
    </div>
  ),
}));

interface YAxisConfigurationModalProps {
  visible: boolean;
  onClose: () => void;
  onSave: (config: YAxisConfig) => void;
  initialConfig: YAxisConfig;
  metrics: MetricConfig[];
}

const YAxisConfigurationModal: React.FC<YAxisConfigurationModalProps> = ({
  visible,
  onClose,
  onSave,
  initialConfig,
  metrics,
}) => {
  const [config, setConfig] = useState<YAxisConfig>(initialConfig);

  useEffect(() => {
    if (visible) {
      setConfig(initialConfig || {});
    }
  }, [visible, initialConfig]);

  const handleChange = (
    id: string,
    key: keyof SingleYAxisConfig,
    value: any
  ) => {
    setConfig((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [key]: value,
      },
    }));
  };

  return (
    <Modal
      title="Configure Y-Axis"
      open={visible}
      onCancel={onClose}
      centered
      width={600}
      footer={[
        <Button
          key="reset"
          onClick={() => setConfig({})}
          style={{ float: "left" }}
        >
          Reset
        </Button>,
        <Button key="cancel" onClick={onClose}>
          Cancel
        </Button>,
        <Button key="submit" type="primary" onClick={() => onSave(config)}>
          OK
        </Button>,
      ]}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          paddingTop: "16px",
        }}
      >
        {metrics.map((metric) => {
          const metricConfig = config[metric.id] || {};
          return (
            <div key={metric.id}>
              {/* Metric Label */}
              <div
                style={{
                  fontWeight: 600,
                  fontSize: "14px",
                  marginBottom: "8px",
                  color: "#1f2937",
                }}
              >
                {metric.label}
              </div>

              {/* Configuration Row */}
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  justifyContent: "space-between",
                  gap: "24px",
                }}
              >
                {/* Range (Min - Max) */}
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#6b7280",
                      marginBottom: "6px",
                    }}
                  >
                    Range (Min - Max)
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <InputNumber
                      placeholder="Min"
                      value={metricConfig.min}
                      onChange={(val) => handleChange(metric.id, "min", val)}
                      style={{ width: "80px" }}
                      size="middle"
                    />
                    <InputNumber
                      placeholder="Max"
                      value={metricConfig.max}
                      onChange={(val) => handleChange(metric.id, "max", val)}
                      style={{ width: "80px" }}
                      size="middle"
                    />
                  </div>
                </div>

                {/* Color */}
                <div>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#6b7280",
                      marginBottom: "6px",
                    }}
                  >
                    Color
                  </div>
                  <Select
                    value={metricConfig.color}
                    onChange={(val) => handleChange(metric.id, "color", val)}
                    style={{ width: "120px" }}
                    options={COLOR_OPTIONS}
                    placeholder="Select"
                  />
                </div>

                {/* Position */}
                <div>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#6b7280",
                      marginBottom: "6px",
                      textAlign: "right",
                    }}
                  >
                    Position
                  </div>
                  <Radio.Group
                    value={metricConfig.position || "left"}
                    onChange={(e: RadioChangeEvent) =>
                      handleChange(metric.id, "position", e.target.value)
                    }
                    optionType="button"
                    buttonStyle="solid"
                  >
                    <Radio.Button value="left">Left</Radio.Button>
                    <Radio.Button value="right">Right</Radio.Button>
                  </Radio.Group>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Modal>
  );
};

export default YAxisConfigurationModal;
