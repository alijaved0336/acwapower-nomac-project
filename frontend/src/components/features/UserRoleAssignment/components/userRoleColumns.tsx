"use client";

import React from "react";
import type { ColumnsType } from "antd/es/table";
import { Space, Avatar, Button, Tag, Typography } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { BackendUser } from "../../../../types/api.types";
import { BackendRole } from "../../../../types";

const { Text } = Typography;

export type UserRoleColumnsDeps = {
  // helpers
  getRoleName: (userRole: string) => string;
  getRoleType: (userRole: string) => string;
  getRoleTypeColor: (type: string) => string;
  getRoleTypeIcon: (type: string) => React.ReactNode;

  // actions
  handleAssignRole: (user: BackendUser) => void;

  handleViewUserDetails: (user: BackendUser) => void;
  doRevoke: (userRoleId: string, userId?: string) => void | Promise<void>;

  // flags
  revoking: boolean;
};
export function makeUserRoleColumns({
  getRoleName,
  getRoleType,
  getRoleTypeColor,
  getRoleTypeIcon,
  handleAssignRole,
  handleViewUserDetails,
  doRevoke,
  revoking,
}: UserRoleColumnsDeps): ColumnsType<BackendUser> {
  const cols: ColumnsType<BackendUser> = [
    {
      title: "User",
      key: "user",
      render: (_: any, record: BackendUser) => (
        <Space>
          <Avatar
            src={record.picture ?? undefined}
            icon={<UserOutlined />}
            size="default"
          />
          <div>
            <Button
              type="link"
              style={{ padding: 0, height: "auto", fontWeight: "bold" }}
              onClick={() => handleViewUserDetails(record)}
            >
              {record.name}
            </Button>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: "Roles",
      dataIndex: "roles",
      key: "roles",
      render: (_: any, record: BackendUser) => {
        return (
          <Space wrap>
            <Tag
              key={record?.id}
              color={getRoleTypeColor(record?.role?.type ?? "user")}
              icon={getRoleTypeIcon(record?.role?.type ?? "user")}
            >
              {record?.role?.name}
            </Tag>
          </Space>
        );
      },
    },
    {
      title: "Notes",
      key: "clusterAccess",
      render: (_: any, record: BackendUser) => {
        const role: BackendRole = record.role!;
        const clusters = role?.clusters;
        return clusters?.length ? (
          <Tag color="blue">{clusters.length} clusters</Tag>
        ) : (
          <Text type="secondary">No access</Text>
        );
      },
    },
    {
      title: "Last Updated",
      dataIndex: "updated_at",
      key: "updated_at",
      render: (date: string) =>
        date ? new Date(date).toLocaleDateString() : "Never",
    },
  ];

  return cols;
}
