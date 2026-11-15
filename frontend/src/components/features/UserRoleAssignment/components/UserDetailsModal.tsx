"use client";

import React, { useState } from "react";
import {
  Modal,
  Card,
  Space,
  Avatar,
  Typography,
  Tag,
  Button,
  Row,
  Col,
  message,
  List,
  Divider,
  theme,
} from "antd";
import {
  UserOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";
import type { UserDetailsModalProps } from "@/types/role.types";
import { useUserDetailsData } from "../hooks/useUserDetailsData";
import {
  getRoleTypeColor,
  getRoleTypeIcon,
} from "../../../../utils/userRole.helpers";

const { Title, Text } = Typography;

const UserDetailsModal: React.FC<UserDetailsModalProps> = ({
  visible,
  user,
  onCancel,
  onUserUpdated,
  onAssignRole,
}) => {
  const { token } = theme.useToken();

  const { rolesLoading, getRoleDetails } = useUserDetailsData(visible, user);

  if (!user) return null;

  const renderActiveRoles = () => {
    if (!user.role_id) {
      return (
        <div style={{ padding: "12px 0", textAlign: "center" }}>
          <Text type="secondary" style={{ fontSize: "13px" }}>
            No role assigned
          </Text>
        </div>
      );
    }

    const roleId = user.role_id;
    const roleDetails = getRoleDetails(roleId);
    const roleType = roleDetails?.type || "user";

    return (
      <List.Item
        style={{
          padding: "12px 0",
          border: "none",
        }}
      >
        <Space direction="vertical" size="small" style={{ width: "100%" }}>
          <Space
            size="middle"
            style={{ width: "100%", justifyContent: "space-between" }}
          >
            <Tag
              color={getRoleTypeColor(roleType)}
              icon={getRoleTypeIcon(roleType)}
              style={{ margin: 0, fontSize: "13px", padding: "4px 12px" }}
            >
              {roleDetails?.name || roleId}
            </Tag>
            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => onAssignRole(user)}
              disabled={rolesLoading}
            >
              Assign Role
            </Button>
          </Space>
          {roleDetails?.description && (
            <Text type="secondary" style={{ fontSize: "12px" }}>
              {roleDetails.description}
            </Text>
          )}
        </Space>
      </List.Item>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const year = date.getFullYear();
    return `${month}/${day}/${year}`;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);

    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const year = date.getFullYear();

    let hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12;
    const hoursStr = String(hours).padStart(2, "0");

    return `${month}/${day}/${year}, ${hoursStr}:${minutes}:${seconds} ${ampm}`;
  };

  return (
    <Modal
      title={null}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
      styles={{ body: { padding: 0 } }}
      confirmLoading={rolesLoading}
      destroyOnHidden
    >
      {/* Header Section with Gradient */}
      <div
        style={{
          padding: "20px 24px",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          borderRadius: "8px 8px 0 0",
          marginTop: "16px",
        }}
      >
        <Space size="middle">
          <Avatar
            src={user.picture || undefined}
            icon={<UserOutlined />}
            size={64}
            style={{ border: "3px solid white" }}
          />
          <div>
            <Title level={4} style={{ margin: 0, color: "white" }}>
              {user.name}
            </Title>
            <Text style={{ color: "rgba(255,255,255,0.9)", fontSize: "13px" }}>
              {user.email}
            </Text>
          </div>
        </Space>
      </div>

      <div style={{ padding: "20px 24px" }}>
        {/* Quick Stats - 3 Column Grid */}
        <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
          {/* Status Card */}
          <Col span={8}>
            <Card
              size="small"
              styles={{ body: { padding: "12px" } }}
              style={{
                transition: "all 0.3s ease",
                height: "100%",
              }}
            >
              <Space direction="vertical" size={4}>
                <Text type="secondary" style={{ fontSize: "12px" }}>
                  Status
                </Text>
                <Tag
                  icon={
                    user.is_active ? (
                      <CheckCircleOutlined />
                    ) : (
                      <CloseCircleOutlined />
                    )
                  }
                  color={user.is_active ? "success" : "error"}
                  style={{ margin: 0 }}
                >
                  {user.is_active ? "Active" : "Inactive"}
                </Tag>
              </Space>
            </Card>
          </Col>

          {/* Created Card */}
          <Col span={8}>
            <Card
              size="small"
              styles={{ body: { padding: "12px" } }}
              style={{
                transition: "all 0.3s ease",
                height: "100%",
              }}
            >
              <Space direction="vertical" size={4}>
                <Text type="secondary" style={{ fontSize: "12px" }}>
                  Created
                </Text>
                <Text
                  strong
                  style={{
                    fontSize: "13px",
                    display: "block",
                    whiteSpace: "nowrap",
                  }}
                >
                  {formatDate(user.created_at)}
                </Text>
              </Space>
            </Card>
          </Col>

          {/* Last Updated Card */}
          <Col span={8}>
            <Card
              size="small"
              styles={{ body: { padding: "12px" } }}
              style={{
                transition: "all 0.3s ease",
                height: "100%",
              }}
            >
              <Space direction="vertical" size={4}>
                <Text type="secondary" style={{ fontSize: "12px" }}>
                  Last Updated
                </Text>
                <Text
                  strong
                  style={{
                    fontSize: "11px",
                    display: "block",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user.updated_at ? formatDateTime(user.updated_at) : "Never"}
                </Text>
              </Space>
            </Card>
          </Col>
        </Row>

        <Divider style={{ margin: "16px 0" }} />

        {/* Active Roles Section */}
        <div>
          <Text
            strong
            style={{ fontSize: "14px", marginBottom: 12, display: "block" }}
          >
            Active Role
          </Text>

          <Card
            size="small"
            loading={rolesLoading}
            styles={{
              body: {
                padding: "8px 16px",
                background: token.colorBgElevated,
              },
            }}
          >
            {renderActiveRoles()}
          </Card>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          padding: "12px 24px",
          borderTop: `1px solid ${token.colorBorder}`,
          textAlign: "right",
        }}
      >
        <Button onClick={onCancel}>Close</Button>
      </div>
    </Modal>
  );
};

export default UserDetailsModal;
