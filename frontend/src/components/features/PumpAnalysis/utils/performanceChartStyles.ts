export const performanceChartGlobalStyles = `
  .performance-chart-wrapper {
    position: relative;
  }
  .performance-chart-wrapper .mb-3 {
    position: absolute !important;
    top: -44px !important;
    right: 0 !important;
    left: auto !important;
    margin-bottom: 0 !important;
    z-index: 10;
    padding: 0 !important;
  }
  .performance-chart-wrapper .mb-3 > span {
    display: none !important;
  }
  .performance-chart-wrapper .mb-3 > div {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
  }
  .speed-select .ant-select-selector {
    display: flex !important;
    align-items: center !important;
    padding: 4px 11px !important;
  }
  .speed-select:not(.ant-select-disabled) .ant-select-selection-placeholder {
    display: flex !important;
    align-items: center !important;
    line-height: 30px !important;
    color: #000000 !important;
  }
  .speed-select:not(.ant-select-disabled) .ant-select-selection-item {
    display: flex !important;
    align-items: center !important;
    line-height: 22px !important;
    color: #000000 !important;
  }
  .speed-select .ant-select-selection-overflow {
    display: flex !important;
    align-items: center !important;
  }
`;

export const filtersContainerStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  marginBottom: "12px",
  gap: "16px",
};

export const leftFiltersStyle = {
  display: "flex",
  gap: "10px",
  alignItems: "center",
};

export const rightFiltersStyle = {
  display: "flex",
  gap: "10px",
  alignItems: "center",
  paddingRight: "180px",
};

export const noDataStyle = {
  position: "absolute" as const,
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  zIndex: 10,
  fontSize: "14px",
  color: "#8c8c8c",
};

export const loadingContainerStyle = {
  textAlign: "center" as const,
  padding: "200px 0",
  minHeight: "500px",
};
