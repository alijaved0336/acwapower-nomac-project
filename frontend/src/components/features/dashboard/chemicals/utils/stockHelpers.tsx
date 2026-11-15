import React from "react";
import { Card, Row, Col, Typography, Skeleton } from "antd";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/stockLayout.module.css";

const { Text } = Typography;

export const renderSkeletonCards = (
  count: number,
  colProps: any,
  cardStyle: any,
  cardBodyStyle: any,
  dataRowStyle: any
) => (
  <Row gutter={[12, 12]}>
    {Array.from({ length: count }).map((_, idx) => (
      <Col {...colProps} key={`skeleton-${idx}`}>
        <Card
          className={cn(layoutStyles.stockCard)}
          style={cardStyle}
          styles={{ body: cardBodyStyle }}
        >
          <Skeleton.Input
            active
            size="small"
            style={{ width: "60%", marginBottom: "12px" }}
          />
          {Array.from({ length: 9 }).map((_, rowIdx) => (
            <div key={rowIdx} style={dataRowStyle}>
              <Skeleton.Input active size="small" style={{ width: "40%" }} />
              <Skeleton.Input active size="small" style={{ width: "45%" }} />
            </div>
          ))}
        </Card>
      </Col>
    ))}
  </Row>
);

export const renderEmptyCards = (
  count: number,
  colProps: any,
  cardStyle: any,
  cardBodyStyle: any,
  dimColor?: string
) => (
  <Row gutter={[12, 12]}>
    {Array.from({ length: count }).map((_, idx) => (
      <Col {...colProps} key={`empty-${idx}`}>
        <Card
          className={cn(layoutStyles.stockCard)}
          style={cardStyle}
          styles={{
            body: {
              ...cardBodyStyle,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: "200px",
            },
          }}
        >
          <Text style={{ fontSize: "14px", color: dimColor || "#bfbfbf" }}>
            No Data
          </Text>
        </Card>
      </Col>
    ))}
  </Row>
);

export const renderDataRow = (
  item: any,
  idx: number,
  dataRowStyle: any,
  labelStyle: any,
  valueStyle: any,
  dimValueStyle: any,
  unitStyle: any,
  isPlaceholder: (val: string) => boolean
) => {
  // For simple rows (Level 1, Level 2, Stock)
  if (item.value !== "") {
    return (
      <div key={idx} style={dataRowStyle}>
        <Text style={labelStyle}>{item.label}</Text>
        <div>
          <Text style={isPlaceholder(item.value) ? dimValueStyle : valueStyle}>
            {item.value}
          </Text>
          {item.unit && <Text style={unitStyle}>{item.unit}</Text>}
        </div>
      </div>
    );
  }

  // For Line 1, Line 2, Total rows
  return (
    <div key={idx}>
      <div style={{ ...dataRowStyle, marginTop: idx > 3 ? "8px" : 0 }}>
        <Text style={{ ...labelStyle, fontWeight: 600 }}>{item.label}:</Text>
      </div>
      <div style={{ ...dataRowStyle, paddingLeft: "12px" }}>
        <Text style={labelStyle}>Measured ppm:</Text>
        <div>
          <Text
            style={isPlaceholder(item.measuredPpm) ? dimValueStyle : valueStyle}
          >
            {item.measuredPpm}
          </Text>
          <Text style={unitStyle}> ppm</Text>
        </div>
      </div>
      <div style={{ ...dataRowStyle, paddingLeft: "12px" }}>
        <Text style={labelStyle}>Measured flow:</Text>
        <div>
          <Text
            style={
              isPlaceholder(item.measuredFlow) ? dimValueStyle : valueStyle
            }
          >
            {item.measuredFlow}
          </Text>
          <Text style={unitStyle}> L/H</Text>
        </div>
      </div>
      <div style={{ ...dataRowStyle, paddingLeft: "12px" }}>
        <Text style={labelStyle}>Expected ppm:</Text>
        <div>
          <Text
            style={isPlaceholder(item.expectedPpm) ? dimValueStyle : valueStyle}
          >
            {item.expectedPpm}
          </Text>
          <Text style={unitStyle}> ppm</Text>
        </div>
      </div>
      <div style={{ ...dataRowStyle, paddingLeft: "12px" }}>
        <Text style={labelStyle}>Expected flow:</Text>
        <div>
          <Text
            style={
              isPlaceholder(item.expectedFlow) ? dimValueStyle : valueStyle
            }
          >
            {item.expectedFlow}
          </Text>
          <Text style={unitStyle}> L/H</Text>
        </div>
      </div>
    </div>
  );
};
