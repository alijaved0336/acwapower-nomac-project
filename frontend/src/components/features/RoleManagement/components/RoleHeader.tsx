import { Typography } from "antd";
import React from "react";
import Header from "@/components/layouts/DashboardLayout/Header";

const RoleHeader = () => {
  return (
    <Header className="mb-4 flex items-center justify-between">
      <Typography.Title level={3} style={{ margin: 0, padding: "12px" }}>
        Role Management
      </Typography.Title>
    </Header>
  );
};

export default RoleHeader;
