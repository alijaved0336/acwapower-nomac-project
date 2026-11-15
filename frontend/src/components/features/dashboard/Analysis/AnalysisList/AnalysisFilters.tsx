import React, { useState } from "react";
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
  DatePicker,
} from "antd";

const { RangePicker } = DatePicker;

import {
  FilterOutlined,
  SettingOutlined,
  SearchOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useAnalysisList } from "../context/AnalysisListContext";
import dayjs from "dayjs";
import DateRangePicker from "../../../../common/widgets/DateRangePicker";
import { DateFormat } from "../../../../../constants/enums";
import CreateAnalysisModal from "../AnalysisTemplate/CreateAnalysisModal";

const AnalysisFilters = () => {
  const [open, setOpen] = useState(false);

  const {
    visibleCols,
    columnDefs,
    search,
    visibilityFilter,
    dateFilter,
    setVisibleCols,
    handleSearch,
    handleVisibilityFilter,
    handleDatesChange,
    applyFilters,
    resetFilters,
  } = useAnalysisList();

  const filtersContent = (
    <div>
      <Typography.Text strong>Filters</Typography.Text>
      <Divider style={{ margin: "8px 0" }} />
      <Space direction="vertical" style={{ width: "100%" }}>
        {/* <div>
          <Typography.Text type="secondary">Template Type</Typography.Text>
          <Select
            // value={filters.type}
            // onChange={(v) => setFilters((f) => ({ ...f, type: v as any }))}
            options={[
              { value: "All" },
              { value: "Classification" },
              { value: "Instance" },
            ]}
            style={{ width: "100%" }}
          />
        </div> */}
        <div>
          <Typography.Text type="secondary">Visibility</Typography.Text>
          <Select
            value={visibilityFilter}
            onChange={handleVisibilityFilter}
            options={[
              { value: "All" },
              { value: "Public" },
              { value: "Private" },
            ]}
            style={{ width: "100%" }}
          />
        </div>
        <Divider style={{ margin: "8px 0" }} />

        <div>
          <Typography.Text type="secondary">Created At</Typography.Text>

          <div>
            <DateRangePicker
              showTime={false}
              onChange={handleDatesChange}
              size="middle"
              disableFutureDates
              value={
                dateFilter
                  ? [
                      dayjs(dateFilter.from_date, DateFormat.DATE_ONLY),
                      dayjs(dateFilter.to_date, DateFormat.DATE_ONLY),
                    ]
                  : null
              }
              allowClear={true}
            />
          </div>
        </div>

        <Divider style={{ margin: "8px 0" }} />
        <Flex justify="flex-end" gap={8}>
          <Button onClick={resetFilters}>Reset</Button>
          <Button type="primary" onClick={applyFilters}>
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
    <div className="mb-16 flex flex-row-reverse flex-wrap items-center justify-between gap-8">
      <Space className="ml-auto">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setOpen(!open)}
        >
          Create Analysis
        </Button>
      </Space>
      <Space>
        <Popover
          placement="bottomRight"
          trigger={["click"]}
          content={columnsContent}
        >
          <Button icon={<SettingOutlined />}>Columns</Button>
        </Popover>
        <Popover
          placement="bottomRight"
          trigger={["click"]}
          content={filtersContent}
        >
          <Button icon={<FilterOutlined />}>Filters</Button>
        </Popover>
      </Space>

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

      <CreateAnalysisModal
        open={open}
        onClose={() => setOpen(false)}
        defaultValues={{
          user_id: "",
          asset_type: "asasa",
          type: "SWRO Plant",
          visibility: "private",
        }}
      />
    </div>
  );
};

export default AnalysisFilters;
