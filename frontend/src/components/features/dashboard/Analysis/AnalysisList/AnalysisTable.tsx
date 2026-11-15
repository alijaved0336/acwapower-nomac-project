import React, { useMemo } from "react";
import { Tag, Typography } from "antd";
import { theme } from "antd";
import Pagination from "../../../../common/widgets/Pagination";
import { Analysis } from "@/types/analysis.types";
import { useAnalysisList } from "../context/AnalysisListContext";
import { getFormattedDate } from "../../../../../utils/helpers";
import { BinIcon, EyeIcon, ShareIcon } from "../../../../../assets/icons";
import Table from "../../../../common/Table";
import { useRouter } from "next/navigation";
import { cn } from "../../../../../utils";
import { useAppSelector } from "../../../../../hooks";

const AnalysisTable = () => {
  const {
    analysisList,
    isFetchingAnalysis,
    total,
    filters,
    visibleCols,
    handlePaginationChange,
    handleOpenRemoveAnaysisModal,
  } = useAnalysisList();

  const router = useRouter();
  const user = useAppSelector((state) => state.auth.user);

  // Inside your component:
  const { token } = theme.useToken();

  const columns = useMemo(() => {
    const cols = [
      {
        title: "ID",
        dataIndex: "id",
        key: "id",
      },
      {
        title: "Template Name",
        dataIndex: "name",
        key: "name",
      },

      {
        title: "Subsystem/Asset Type",
        dataIndex: "asset_type",
        key: "asset_type",
      },
      {
        title: "Visibility",
        dataIndex: "visibility",
        key: "visibility",
        render: (v: Analysis["visibility"]) => (
          <Tag color={v === "public" ? "blue" : "purple"}>
            {v === "public" ? "Public" : "Private"}
          </Tag>
        ),
      },
      {
        title: "Created By",
        dataIndex: "user_name",
        key: "user_name",
        render: (v: Analysis["user_name"]) => (
          <Typography.Text>{v}</Typography.Text>
        ),
      },

      {
        title: "Updated At",
        dataIndex: "updated_at",
        key: "updated_at",
        render: (v: Analysis["updated_at"]) => getFormattedDate(v),
      },
      {
        title: "Action",
        dataIndex: "action",
        key: "action",
        fixed: "right",
        render: (_: any, analysis: Analysis) => {
          return (
            <div
              className={cn("flex items-center", {
                "gap-8": user?.role?.type === "super_admin",
              })}
            >
              <EyeIcon
                className="cursor-pointer"
                onClick={() =>
                  router.push(
                    `/dashboard/analysis/${analysis.id}?name=${encodeURIComponent(analysis.name)}&visibility=${analysis.visibility}`
                  )
                }
              />
              {user?.role?.type === "super_admin" && (
                <BinIcon
                  className="cursor-pointer"
                  onClick={() => handleOpenRemoveAnaysisModal(analysis)}
                />
              )}
            </div>
          );
        },
      },
    ].filter((c: any) => visibleCols.includes(c.key));

    return cols as any;
  }, [visibleCols, router, user, handleOpenRemoveAnaysisModal]);

  return (
    <div
      style={{
        overflow: "hidden",
        borderRadius: "12px",
        border: `1px solid ${token.colorBorder}`,
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
        background: token.colorBgContainer,
      }}
    >
      {/* Table Title */}
      <div
        style={{
          padding: "10px 14px",
          background: token.colorBgElevated,
          borderBottom: `1px solid ${token.colorBorder}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span
            style={{
              fontSize: "15px",
              fontWeight: 700,
              color: token.colorText,
              letterSpacing: "0.5px",
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            Analysis
          </span>
        </div>
      </div>
      <Table
        rowKey="id"
        className="!h-[calc(100vh-275px)]"
        data={analysisList}
        columns={columns}
        pagination={false}
        borderRadius={0}
        scroll={{ y: "calc(100% - 55px)" }}
        loading={isFetchingAnalysis}
      />

      <div
        className="!p-8"
        style={{
          background: token.colorBgContainer,
          borderTop: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <Pagination
          showSizeChanger
          onChange={handlePaginationChange}
          total={total}
          current={filters.page}
          pageSize={filters.limit}
          showTotal={(total) => `Total ${total} rows`}
        />
      </div>
    </div>
  );
};

export default AnalysisTable;
