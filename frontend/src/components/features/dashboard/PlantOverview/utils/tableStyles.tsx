// TableStyle.ts
import { CSSProperties } from "react";

export const tableWrapperStyle: CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: 8,
  border: "1px solid #F0F0F0",
  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.06)",
  overflow: "hidden",
  transition: "box-shadow 0.2s ease-in-out",
};

export const tableHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "12px 16px",
  borderBottom: "1px solid #F5F5F5",
  backgroundColor: "#FAFAFA",
};

export const tableTitleStyle: CSSProperties = {
  margin: 0,
  fontWeight: 600,
  color: "#1E1E1E",
  fontSize: "1rem",
};

export const tableStyles = `
  .ant-table-tbody > tr > td {
    font-size: 0.813rem;
    padding: 8px 12px;
  }
  .ant-table-thead > tr > th {
    background: #F9FAFB;
    font-weight: 600;
    color: #444;
  }
  .ant-table-tbody > tr.bg-bg-container {
    background: #FCFCFC;
  }
`;
export const tableStyle: CSSProperties = {
  width: "100%",
  borderRadius: "inherit",
};

export const tableRowEvenStyle = {
  backgroundColor: "#FCFCFC",
};

export const tableHoverStyle = `
  .custom-ant-table .ant-table-tbody > tr:hover {
    background-color: #F5F9FF !important;
    transition: background 0.2s ease-in-out;
  }
`;

export const tableHeaderCSS = `
  .custom-ant-table .ant-table-thead > tr > th {
    background-color: #FAFAFA !important;
    font-weight: 600 !important;
    color: #262626 !important;
    border-bottom: 1px solid #F0F0F0 !important;
  }
`;

export const tableHoverShadow = `
  .custom-table-wrapper:hover {
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
  }
`;
