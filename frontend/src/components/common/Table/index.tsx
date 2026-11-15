"use client";

import { Flex, Table as AntTable, Typography, Input, theme } from "antd";
import type { TablePaginationConfig, TableProps } from "antd";
import {
  useState,
  type CSSProperties,
  type FC,
  KeyboardEvent,
  ChangeEvent,
  useRef,
} from "react";
import { paddingToken } from "../../../styles/themes/tokens/padding";
import { sizeToken } from "../../../styles/themes/tokens/size";
import { cn } from "../../../utils";
import { TableRef } from "antd/es/table";

type IProps = {
  title?: string;
  rowKey?: TableProps<any>["rowKey"];
  tableActions?: React.ReactNode;
  columns: NonNullable<TableProps<any>["columns"]>;
  data: TableProps<any>["dataSource"];
  pagination?: TableProps<any>["pagination"];
  loading?: TableProps<any>["loading"];
  borderRadius?: number;
  className?: string;
  rootClassName?: string;
  titlePaddingInline?: number | string;
  style?: CSSProperties;
} & Omit<TableProps<any>, "columns" | "title" | "dataSource">;

const Table: FC<IProps> = ({
  rowKey,
  className,
  rootClassName,
  columns,
  loading,
  title,
  tableActions,
  borderRadius,
  titlePaddingInline,
  style,
  pagination,
  scroll,
  data,
  ...rest
}) => {
  const { token } = theme.useToken();
  return (
    <div
      style={{
        backgroundColor: token.colorBgContainer,
        // borderRadius: borderRadius ?? sizeToken.sizeMS,
        // border: `1px solid #F5F5F5`,
        overflow: "hidden",
        height: "100%",
      }}
    >
      {title && (
        <Flex
          justify="space-between"
          align="center"
          style={{
            paddingInline: titlePaddingInline ?? paddingToken.paddingLG,
            paddingBlock: paddingToken.paddingLG,
          }}
        >
          <Typography.Title level={3}>{title}</Typography.Title>
          {tableActions}
        </Flex>
      )}

      <AntTable
        {...rest}
        style={{
          width: "100%",
          borderRadius: "inherit",
          ...style,
        }}
        rowKey={rowKey}
        className={cn("edge-to-edge-table custom-scroller", className, {
          "empty-table": !data || data.length === 0,
        })}
        rootClassName={rootClassName}
        scroll={{ x: "max-content", ...scroll }}
        columns={columns}
        loading={loading}
        dataSource={data}
        rowClassName={undefined}
        pagination={pagination ?? false}
      />

      <style>{`
        .ant-pagination-total-text {
          margin-right: auto !important;
        }
      `}</style>
    </div>
  );
};

export default Table;
