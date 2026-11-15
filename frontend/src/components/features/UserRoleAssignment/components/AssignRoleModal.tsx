"use client";

import React from "react";
import {
  Modal,
  Form,
  Select,
  Button,
  Space,
  Typography,
  Avatar,
  message,
  Skeleton,
} from "antd";
import { UserOutlined } from "@ant-design/icons";

import { useAssignRoleMutation, useGetRolesQuery } from "@/store/api/roleApi";
import { getRoleTypeIcon } from "../../../../utils/userRole.helpers";
import { AssignRoleForm, BackendUser } from "../../../../types/api.types";
import { BackendRole } from "../../../../types";

const { Text } = Typography;

interface AssignRoleModalProps {
  visible: boolean;
  user: BackendUser;
  onCancel: () => void;
  onSuccess: () => void;
}

const AssignRoleModal: React.FC<AssignRoleModalProps> = ({
  visible,
  user,
  onCancel,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [assignRole, { isLoading: submitting }] = useAssignRoleMutation();

  // Fetch roles (lazy load when modal opens)
  const { data: rolesRes, isFetching: loadingRoles } = useGetRolesQuery(
    {},
    { skip: !visible }
  );
  const roles: BackendRole[] = rolesRes?.items ?? [];

  const handleSubmit = async (values: { roleId: string }) => {
    try {
      const payload: AssignRoleForm = {
        userId: user.id,
        roleId: values.roleId,
      };
      await assignRole(payload).unwrap();
      message.success("Role assigned successfully");
      onSuccess();
    } catch (e) {
      console.error(e);
      message.error("Failed to assign role");
    }
  };

  return (
    <Modal
      title={`Assign Role to ${user.name}`}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
      destroyOnHidden
      confirmLoading={loadingRoles}
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Avatar src={user.picture ?? undefined} icon={<UserOutlined />} />
          <div>
            <Text strong>{user.name}</Text>
            <br />
            <Text type="secondary">{user.email}</Text>
          </div>
        </Space>
      </div>

      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item
          label="Select Role"
          name="roleId"
          rules={[{ required: true, message: "Please select a role" }]}
        >
          {loadingRoles ? (
            <Skeleton.Input active block style={{ height: 40 }} />
          ) : (
            <Select
              placeholder="Choose a role"
              size="large"
              optionLabelProp="label"
              showSearch
              filterOption={(input, option) =>
                (option?.label as string)
                  ?.toLowerCase()
                  .includes(input.toLowerCase())
              }
            >
              {roles.map((role) => (
                <Select.Option
                  key={role.id}
                  value={role.id}
                  label={
                    <Space>
                      {getRoleTypeIcon(role.type)}
                      <span>{role.name}</span>
                    </Space>
                  }
                >
                  <Space align="start">
                    {getRoleTypeIcon(role.type)}
                    <div>
                      <div style={{ fontWeight: 500 }}>{role.name}</div>
                    </div>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          )}
        </Form.Item>

        <div style={{ textAlign: "right" }}>
          <Space>
            <Button onClick={onCancel}>Cancel</Button>
            <Button type="primary" htmlType="submit" loading={submitting}>
              Assign Role
            </Button>
          </Space>
        </div>
      </Form>
    </Modal>
  );
};

export default AssignRoleModal;
