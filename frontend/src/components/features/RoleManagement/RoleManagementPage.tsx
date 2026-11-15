"use client";

import React from "react";
import { Card } from "antd";

import CompactStatusBar from "@/components/common/CompactStatusBar";
import RoleFilters from "./components/RoleFilters";
import RoleTable from "./components/RoleTable";
import {
  RoleManagementProvider,
  useRoleManagement,
} from "./context/RoleManagementContext";
import CreateRoleModal from "./components/CreateRoleModal";

const RoleManagementContent = () => {
  const {
    modalVisible,
    modalMode,
    selectedRole,
    closeModal,
    handleCreateSuccess,
    handleUpdateSuccess,
  } = useRoleManagement();

  return (
    <>
      <CompactStatusBar
        activeTab="all"
        onTabChange={() => {}}
        siteName="Role Management"
        dateRangeText=""
        customTabs={[]}
      />
      <div className="mt-8 px-16">
        <Card className="card">
          <RoleFilters />
          <RoleTable />
        </Card>
      </div>
      <CreateRoleModal
        visible={modalVisible}
        mode={modalMode}
        role={selectedRole}
        onCancel={closeModal}
        onSuccess={
          modalMode === "create" ? handleCreateSuccess : handleUpdateSuccess
        }
      />
    </>
  );
};

const RoleManagementPage: React.FC = () => {
  return (
    <RoleManagementProvider>
      <RoleManagementContent />
    </RoleManagementProvider>
  );
};

export default RoleManagementPage;
