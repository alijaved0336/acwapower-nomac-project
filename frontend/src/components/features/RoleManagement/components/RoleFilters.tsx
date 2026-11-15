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
  PlusOutlined,
} from "@ant-design/icons";
import { useRoleManagement } from "../context/RoleManagementContext";

const RoleFilters = () => {
  const {
    visibleCols,
    columnDefs,
    search,
    typeFilter,
    setVisibleCols,
    handleSearch,
    handleTypeFilter,
    applyFilters,
    resetFilters,
    canManageRoles,
    openCreateModal,
  } = useRoleManagement();

  const [localTypeFilter, setLocalTypeFilter] = useState<string | null>(
    typeFilter || null
  );

  useEffect(() => {
    setLocalTypeFilter(typeFilter || null);
  }, [typeFilter]);

  const handleTypeChange = (value: string | null) => {
    setLocalTypeFilter(value);
    handleTypeFilter(value);
  };

  const handleApply = () => {
    applyFilters();
  };

  const handleReset = () => {
    setLocalTypeFilter(null);
    resetFilters();
  };

  const filtersContent = (
    <div>
      <Typography.Text strong>Filters</Typography.Text>
      <Divider style={{ margin: "8px 0" }} />
      <Space direction="vertical" style={{ width: "100%" }}>
        <div>
          <Typography.Text type="secondary">Type</Typography.Text>
          <Select
            placeholder="All Types"
            style={{ width: "100%" }}
            value={localTypeFilter}
            onChange={handleTypeChange}
            allowClear
            size="middle"
            options={[
              { value: "super_admin", label: "Super Admin" },
              { value: "user", label: "User" },
            ]}
          />
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
    <div className="mb-16 flex flex-wrap items-center justify-between gap-8">
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
      {canManageRoles && (
        <Space className="ml-auto">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={openCreateModal}
          >
            Create Role
          </Button>
        </Space>
      )}
    </div>
  );
};

export default RoleFilters;
