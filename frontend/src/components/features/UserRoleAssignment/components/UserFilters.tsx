import React, { useState, useEffect } from "react";
import {
  Button,
  Checkbox,
  Divider,
  Flex,
  Input,
  Popover,
  Select,
  Space,
  Typography,
} from "antd";

import {
  FilterOutlined,
  SettingOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { useUserManagement } from "../context/UserManagementContext";
import { getRoleTypeIcon } from "@/utils/userRole.helpers";

const UserFilters = () => {
  const {
    visibleCols,
    columnDefs,
    search,
    roleFilter,
    roles,
    rolesLoading,
    setVisibleCols,
    handleSearch,
    handleRoleFilter,
    applyFilters,
    resetFilters,
  } = useUserManagement();

  // Local state for immediate UI updates
  const [localRoleFilter, setLocalRoleFilter] = useState<string | null>(
    roleFilter || null
  );

  // Sync local state when context filter changes (e.g., after reset)
  useEffect(() => {
    setLocalRoleFilter(roleFilter || null);
  }, [roleFilter]);

  const handleRoleChange = (value: string | null) => {
    setLocalRoleFilter(value);
    handleRoleFilter(value);
  };

  const handleApply = () => {
    applyFilters();
  };

  const handleReset = () => {
    setLocalRoleFilter(null);
    resetFilters();
  };

  const filtersContent = (
    <div>
      <Typography.Text strong>Filters</Typography.Text>
      <Divider style={{ margin: "8px 0" }} />
      <Space direction="vertical" style={{ width: "100%" }}>
        <div>
          <Typography.Text type="secondary">Role</Typography.Text>
          <Select
            placeholder="All Roles"
            style={{ width: "100%" }}
            value={localRoleFilter}
            onChange={handleRoleChange}
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
        <Divider style={{ margin: "8px 0" }} />
        <Flex justify="flex-end" gap={8}>
          <Button onClick={handleReset}>Reset</Button>
          <Button type="primary" onClick={handleApply}>
            Apply
          </Button>
        </Flex>
      </Space>
    </div>
  );

  const columnsContent = (
    <div>
      <Typography.Text strong>Columns</Typography.Text>
      <Divider style={{ margin: "8px 8px" }} />
      <Checkbox.Group
        style={{ width: "100%" }}
        value={visibleCols}
        onChange={(v) => setVisibleCols(v)}
      >
        <Flex vertical gap={8}>
          {columnDefs.map((c) => (
            <Checkbox value={c.key} key={c.key}>
              {c.label}
            </Checkbox>
          ))}
        </Flex>
      </Checkbox.Group>
    </div>
  );

  return (
    <div className="mb-16 flex flex-wrap items-center gap-8">
      <div className="flex items-center gap-4">
        <Space.Compact
          style={{ width: 360 }}
          className="mobile-sm:grow mobile:grow-0"
        >
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="Search here..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </Space.Compact>
        <Space>
          <Popover
            placement="bottomLeft"
            trigger={["click"]}
            content={columnsContent}
          >
            <Button icon={<SettingOutlined />}>Columns</Button>
          </Popover>
          <Popover
            placement="bottomLeft"
            trigger={["click"]}
            content={filtersContent}
          >
            <Button icon={<FilterOutlined />}>Filters</Button>
          </Popover>
        </Space>
      </div>
    </div>
  );
};

export default UserFilters;
