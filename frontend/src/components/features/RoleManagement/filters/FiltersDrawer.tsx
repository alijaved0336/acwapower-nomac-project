"use client";

import React from "react";

import { Drawer, Button, Space, Select, Input } from "antd";

const { Option } = Select;

interface FiltersDrawerProps {
  visible: boolean;
  onClose: () => void;
  onReset: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  typeValue?: string;
  onTypeChange: (value?: string) => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({
  visible,
  onClose,
  onReset,
  searchValue,
  onSearchChange,
  typeValue,
  onTypeChange,
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
        {/* Search Filter */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Search
          </label>
          <Input
            placeholder="Search roles..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            allowClear
            size="middle"
          />
        </div>

        {/* Type Filter */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Type
          </label>
          <Select
            placeholder="All Types"
            style={{ width: "100%" }}
            value={typeValue}
            onChange={onTypeChange}
            allowClear
            size="middle"
          >
            <Option value="super_admin">Super Admin</Option>
            <Option value="user">User</Option>
          </Select>
        </div>
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
