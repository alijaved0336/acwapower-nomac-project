"use client";

import React, { useMemo, useCallback } from "react";
import CompactTable from "@/components/common/CompactTable";
import { Space, Tag, Avatar, Typography } from "antd";
import { UserOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { BackendRole } from "@/types/role.types";
import { BackendUser } from "@/types/api.types";

import { getRoleTypeIcon, getRoleTypeColor } from "@/utils/userRole.helpers";

const { Text } = Typography;

interface CompactUserTableProps {
  users: BackendUser[];
  roles: BackendRole[];
  loading?: boolean;
  onRowClick?: (record: BackendUser) => void;
}

const CompactUserTable: React.FC<CompactUserTableProps> = ({
  users,
  roles,
  loading = false,
  onRowClick,
}) => {
  const getRoleById = useCallback(
    (roleId: string | null | undefined) =>
      roles.find((r) => r.id === roleId) ?? null,
    [roles]
  );

  const columns: ColumnsType<BackendUser> = useMemo(
    () => [
      {
        title: "User",
        dataIndex: "name",
        key: "name",
        width: "35%",
        render: (text, record) => (
          <Space size="small">
            <Avatar src={record.picture} icon={<UserOutlined />} size={36} />
            <div>
              <Text
                strong
                style={{ display: "block", fontSize: 12, marginBottom: 2 }}
              >
                {record.name}
              </Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {record.email}
              </Text>
            </div>
          </Space>
        ),
      },
      {
        title: "Roles",
        dataIndex: "role_id",
        key: "roles",
        width: "20%",
        render: (roleId) => {
          const userRole = getRoleById(roleId);
          return (
            <Tag
              icon={
                userRole ? getRoleTypeIcon(userRole.type) : <UserOutlined />
              }
              color={userRole ? getRoleTypeColor(userRole.type) : "default"}
              style={{ fontSize: 11, padding: "2px 8px" }}
            >
              {userRole ? userRole.name : "No Role"}
            </Tag>
          );
        },
      },
      {
        title: "Notes",
        key: "cluster",
        width: "20%",
        render: () => (
          <Tag color="blue" style={{ fontSize: 11, padding: "2px 8px" }}>
            2 clusters
          </Tag>
        ),
      },
      {
        title: "Last Updated",
        dataIndex: "updated_at",
        key: "updated",
        width: "25%",
        render: (date) => (
          <Text type="secondary" style={{ fontSize: 11 }}>
            {date ? new Date(date).toLocaleDateString("en-GB") : "Never"}
          </Text>
        ),
      },
    ],
    [getRoleById]
  );

  return (
    <CompactTable
      data={users}
      columns={columns}
      colorKey="overall"
      loading={loading}
      pageSize={15}
      showPagination={false} // We'll handle pagination in the parent
      showTimeDisplay={false} // Users don't have datetime
      rowKey="id"
      onRowClick={onRowClick}
      scroll={{ x: "100%", y: "max-content" }}
      sticky={{ offsetHeader: 0 }}
    />
  );
};

export default CompactUserTable;
