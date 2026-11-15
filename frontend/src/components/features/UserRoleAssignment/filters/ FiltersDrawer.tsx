// src/components/features/UserRoleAssignment/filters/FiltersDrawer.tsx

"use client";

import React from "react";
import { Drawer, Button, Space, Divider, Select, Input } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { BackendRole } from "@/types/role.types"; // ✅ Using existing type
import { getRoleTypeIcon } from "@/utils/userRole.helpers";

interface FiltersDrawerProps {
  visible: boolean;
  onClose: () => void;
  onReset: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  roleValue?: string;
  onRoleChange: (value?: string) => void;
  roles: BackendRole[];
  rolesLoading: boolean;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({
  visible,
  onClose,
  onReset,
  searchValue,
  onSearchChange,
  roleValue,
  onRoleChange,
  roles,
  rolesLoading,
}) => {
  return (
    <Drawer
      title="Filters"
      placement="right"
      onClose={onClose}
      open={visible}
      width={360}
      extra={
        <Button onClick={onReset} size="small">
          Reset All
        </Button>
      }
    >
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* Role Filter */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Role
          </label>
          <Select
            placeholder="All Roles"
            style={{ width: "100%" }}
            value={roleValue}
            onChange={onRoleChange}
            loading={rolesLoading}
            allowClear
            size="middle"
          >
            {roles.map((role) => (
              <Select.Option key={role.id} value={role.id}>
                <Space>
                  {getRoleTypeIcon(role.type)}
                  {role.name}
                </Space>
              </Select.Option>
            ))}
          </Select>
        </div>
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
