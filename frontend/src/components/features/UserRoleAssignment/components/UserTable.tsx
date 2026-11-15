import React, { useMemo } from "react";
import { theme } from "antd";
import { useAppSelector } from "@/hooks";
import Pagination from "@/components/common/widgets/Pagination";
import { useUserManagement } from "../context/UserManagementContext";
import Table from "@/components/common/Table";
import { makeUserRoleColumns } from "./userRoleColumns";
import { getRoleTypeColor, getRoleTypeIcon } from "@/utils/userRole.helpers";

const UserTable = () => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  const {
    users,
    roles,
    isFetchingUsers,
    total,
    filters,
    visibleCols,
    handlePaginationChange,
    handleViewUserDetails,
    handleAssignRole,
    doRevoke,
    revoking,
  } = useUserManagement();

  const getRoleName = (userRole: string | null | undefined) => {
    // userRole is actually the role_id from the user record
    if (!userRole) return "No Role";
    const role = roles.find((r) => r.id === userRole);
    return role?.name || "No Role";
  };

  const getRoleType = (userRole: string | null | undefined) => {
    // userRole is actually the role_id from the user record
    if (!userRole) return "user";
    const role = roles.find((r) => r.id === userRole);
    return role?.type || "user";
  };

  const columns = useMemo(() => {
    const baseColumns = makeUserRoleColumns({
      getRoleName,
      getRoleType,
      getRoleTypeColor,
      getRoleTypeIcon,
      handleAssignRole,
      handleViewUserDetails,
      doRevoke,
      revoking,
    });

    // Filter columns based on visibleCols
    return baseColumns.filter((c: any) => visibleCols.includes(c.key));
  }, [
    visibleCols,
    handleViewUserDetails,
    handleAssignRole,
    doRevoke,
    revoking,
    getRoleName,
    getRoleType,
  ]);

  return (
    <div
      style={{
        overflow: "hidden",
        borderRadius: "12px",
        border: `1px solid ${token.colorBorder}`,
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
        background: isDark
          ? token.colorBgContainer
          : "linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)",
      }}
    >
      {/* Table Title */}
      <div
        style={{
          padding: "10px 14px",
          background: isDark ? token.colorBgElevated : "#eceff3",
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
            Users
          </span>
        </div>
      </div>
      <Table
        rowKey="id"
        className="!h-[calc(100vh-275px)]"
        data={users}
        columns={columns}
        pagination={false}
        borderRadius={0}
        scroll={{ y: "calc(100% - 55px)" }}
        loading={isFetchingUsers}
        onRow={(record) => ({
          onClick: () => handleViewUserDetails(record),
          style: { cursor: "pointer" },
        })}
      />

      <div className="!p-8">
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

export default UserTable;
