import React from "react";
import { Card, Typography } from "antd";

const { Title, Text } = Typography;

const AccessDenied: React.FC = () => {
  return (
    <Card>
      <div style={{ textAlign: "center", padding: "40px 0" }}>
        <Title level={4}>Access Denied</Title>
        <Text type="secondary">
          You don&apos;t have permission to view users.
        </Text>
      </div>
    </Card>
  );
};

export default AccessDenied;
