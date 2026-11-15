"use client";

import React from "react";
import { Card } from "antd";

import CompactStatusBar from "@/components/common/CompactStatusBar";
import UserFilters from "./components/UserFilters";
import UserTable from "./components/UserTable";
import {
  UserManagementProvider,
  useUserManagement,
} from "./context/UserManagementContext";
import UserDetailsModal from "./components/UserDetailsModal";
import AssignRoleModal from "./components/AssignRoleModal";

const UserManagementContent = () => {
  const {
    selectedUser,
    userDetailsModalVisible,
    assignRoleModalVisible,
    setUserDetailsModalVisible,
    setSelectedUser,
    setAssignRoleModalVisible,
    handleAssignRoleSuccess,
    handleUserUpdated,
    handleAssignRoleFromDetails,
  } = useUserManagement();

  return (
    <>
      <CompactStatusBar
        activeTab="all"
        onTabChange={() => {}}
        siteName="User Management"
        dateRangeText=""
        customTabs={[]}
      />
      <div className="mt-8 px-16">
        <Card className="card">
          <UserFilters />
          <UserTable />
        </Card>
      </div>
      {selectedUser && (
        <>
          <UserDetailsModal
            visible={userDetailsModalVisible}
            user={selectedUser}
            onCancel={() => {
              setUserDetailsModalVisible(false);
              setSelectedUser(null);
            }}
            onUserUpdated={handleUserUpdated}
            onAssignRole={handleAssignRoleFromDetails}
          />
          <AssignRoleModal
            visible={assignRoleModalVisible}
            user={selectedUser}
            onCancel={() => setAssignRoleModalVisible(false)}
            onSuccess={handleAssignRoleSuccess}
          />
        </>
      )}
    </>
  );
};

const UserRoleAssignmentPage: React.FC = () => {
  return (
    <UserManagementProvider>
      <UserManagementContent />
    </UserManagementProvider>
  );
};

export default UserRoleAssignmentPage;
