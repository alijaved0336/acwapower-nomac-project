"use client";

import React, { useMemo } from "react";
import CompactTable from "@/components/common/CompactTable";
import { makeRoleColumns } from "./roleColumns";
import { BackendRole } from "@/types/role.types";

interface CompactRoleTableProps {
  roles: BackendRole[];
  loading?: boolean;
  canManageRoles?: boolean;
  onEdit: (role: BackendRole) => void;
  onDelete: (roleId: string) => void;
}

const CompactRoleTable: React.FC<CompactRoleTableProps> = ({
  roles,
  loading = false,
  canManageRoles = true,
  onEdit,
  onDelete,
}) => {
  const baseColumns = useMemo(() => {
    return makeRoleColumns({
      canManageRoles,
      onEdit,
      onDelete,
    });
  }, [canManageRoles, onEdit, onDelete]);

  return (
    <CompactTable
      data={roles}
      columns={baseColumns}
      colorKey="overall"
      loading={loading}
      pageSize={15}
      showPagination={false} // We'll handle pagination in the parent
      showTimeDisplay={false} // Roles don't have datetime
      rowKey="id"
      scroll={{ x: "100%", y: "max-content" }}
      sticky={{ offsetHeader: 0 }}
    />
  );
};

export default CompactRoleTable;
