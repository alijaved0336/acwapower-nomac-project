import React from "react";
import { Space, Tag, Tooltip, Button, Popconfirm, Typography } from "antd";
import { EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { BackendRole } from "@/types/role.types";
import {
  getRoleTypeColor,
  getRoleTypeIcon,
} from "../../../../utils/userRole.helpers";

const { Text } = Typography;

export function makeRoleColumns(opts: {
  canManageRoles: boolean;
  onEdit: (role: BackendRole) => void;
  onDelete: (roleId: string) => void;
}) {
  const { canManageRoles, onEdit, onDelete } = opts;

  const columns = [
    {
      title: "Role",
      dataIndex: "name",
      key: "name",
      width: "25%",
      render: (name: string, record: BackendRole) => (
        <Space size="small">
          {getRoleTypeIcon(record.type)}
          <div>
            <Text
              strong
              style={{ display: "block", fontSize: 12, marginBottom: 2 }}
            >
              {name}
            </Text>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {record.description || "No description"}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: "Type",
      dataIndex: "type",
      key: "type",
      width: "15%",
      render: (type: string) => (
        <Tag
          color={getRoleTypeColor(type)}
          icon={getRoleTypeIcon(type)}
          style={{ fontSize: 11, padding: "2px 8px" }}
        >
          {type === "super_admin" ? "Super Admin" : "User"}
        </Tag>
      ),
    },
    {
      title: "Clusters",
      dataIndex: "clusters",
      key: "clusters",
      width: "40%",
      render: (
        clusters: { id: string; name: string; sites: string[] }[] = []
      ) =>
        clusters?.length > 0 ? (
          <Space direction="vertical" size={2} style={{ maxWidth: "100%" }}>
            {clusters.map((c) => (
              <div
                key={c.id}
                style={{ display: "flex", alignItems: "center", gap: 4 }}
              >
                <Tag
                  color="blue"
                  style={{ fontSize: 11, padding: "2px 8px", margin: 0 }}
                >
                  {c.name}
                </Tag>
                {c.sites.length > 0 && (
                  <Space size={2} wrap>
                    {c.sites.map((site) => (
                      <Tag
                        key={`${c.name}-${site}`}
                        color="green"
                        style={{ fontSize: 11, padding: "2px 6px", margin: 0 }}
                      >
                        {site}
                      </Tag>
                    ))}
                  </Space>
                )}
              </div>
            ))}
          </Space>
        ) : (
          <Text type="secondary" style={{ fontSize: 11 }}>
            No clusters
          </Text>
        ),
    },
  ] as any[];

  if (canManageRoles) {
    columns.push({
      title: "Actions",
      key: "actions",
      width: "20%",
      render: (_: any, record: BackendRole) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            onClick={() => onEdit(record)}
            style={{ fontSize: 12, padding: "2px 8px" }}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this role?"
            onConfirm={() => onDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="text"
              icon={<DeleteOutlined />}
              danger
              size="small"
              style={{ fontSize: 12, padding: "2px 8px" }}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    });
  }

  return columns;
}
