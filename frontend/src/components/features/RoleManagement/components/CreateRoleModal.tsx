"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  Space,
  message,
  Skeleton,
} from "antd";
import {
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useGetClustersSitesQuery,
} from "@/store/api/roleApi";
import type { BackendRole } from "@/types/role.types";
import { getSiteActualName } from "../../../../utils/siteDisplayNames";

const { Option } = Select;
const { TextArea } = Input;

type Mode = "create" | "edit";

interface RoleModalProps {
  mode: Mode;
  visible: boolean;
  role?: BackendRole | null;
  onCancel: () => void;
  onSuccess: () => void;
}

const RoleModal: React.FC<RoleModalProps> = ({
  mode,
  visible,
  role,
  onCancel,
  onSuccess,
}) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();
  const [createRole, { isLoading: creating }] = useCreateRoleMutation();
  const [updateRole, { isLoading: updating }] = useUpdateRoleMutation();

  const [clustersOpen, setClustersOpen] = useState(false);
  const shouldFetchClusters = visible && clustersOpen;

  const {
    data: clustersRes,
    isFetching: clustersLoading,
    refetch: refetchClusters,
  } = useGetClustersSitesQuery(undefined, { skip: !shouldFetchClusters });

  const clusterOptions = useMemo(
    () =>
      clustersRes?.clusters ??
      ([] as Array<{
        id: string;
        name: string;
        units: number;
        capacity: string;
        plant: string;
        group: "energy" | "water";
        sites: Array<string>;
      }>),
    [clustersRes]
  );

  useEffect(() => {
    if (!visible) return;
    if (mode === "create") {
      form.resetFields();
      form.setFieldsValue({ type: "user", clusters: [] });
    } else if (mode === "edit" && role) {
      const selectedValues = (role.clusters || []).flatMap((c: any) =>
        (c.sites || []).map((s: string) => `${c.name}::${s}`)
      );

      form.setFieldsValue({
        name: role.name,
        type: role.type ?? "user",
        description: role.description ?? "",
        clusters: selectedValues,
      });
    }
  }, [visible, mode, role, form]);

  const handleDropdownVisibleChange = useCallback(
    (open: boolean) => {
      setClustersOpen(open);
      if (open && !clustersRes) refetchClusters();
    },
    [clustersRes, refetchClusters]
  );

  const handleSubmit = async (values: any) => {
    try {
      // Show toast if no site is selected
      if (!values.clusters || values.clusters.length === 0) {
        messageApi.error("Please select at least one site");
        return;
      }

      const clustersMap: Record<string, string[]> = {};
      (values.clusters || []).forEach((val: string) => {
        const [clusterId, site] = val.split("::");
        if (!clustersMap[clusterId]) clustersMap[clusterId] = [];
        clustersMap[clusterId].push(site);
      });

      const payload = {
        name: values.name.trim(),
        type: values.type,
        description: values.description?.trim() ?? "",
        clusters: Object.entries(clustersMap).map(([name, sites]) => ({
          name,
          sites: sites.map((site) => getSiteActualName(site)),
        })),
      };

      if (mode === "create") {
        await createRole(payload).unwrap();
      } else if (mode === "edit" && role?.id) {
        await updateRole({
          id: role.id,
          data: { ...payload, isActive: true },
        }).unwrap();
      }

      onSuccess();
    } catch (e: any) {
      console.error(e);
      messageApi.error(e?.data?.message || "Failed to save role");
    }
  };

  return (
    <>
      {contextHolder}
      <Modal
        title={mode === "create" ? "Create New Role" : "Edit Role"}
        open={visible}
        onCancel={onCancel}
        footer={null}
        width={720}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="type" initialValue="user" hidden>
            <Input type="hidden" />
          </Form.Item>

          <Form.Item
            label="Name"
            name="name"
            rules={[
              { required: true, message: "Please enter role name" },
              {
                min: 2,
                message: "Role name must be at least 2 characters",
              },
            ]}
          >
            <Input placeholder="Enter role name" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
            rules={[
              { required: true, message: "Please enter role description" },
            ]}
          >
            <TextArea
              rows={3}
              placeholder="Describe the role and its purpose"
            />
          </Form.Item>

          <Form.Item label="Clusters & Sites" name="clusters">
            <Select
              mode="multiple"
              placeholder="Select sites by cluster"
              optionFilterProp="children"
              showSearch
              allowClear
              onDropdownVisibleChange={handleDropdownVisibleChange}
              loading={clustersLoading}
              dropdownRender={(menu) =>
                clustersLoading ? (
                  <div style={{ padding: 12 }}>
                    <Skeleton active title={false} paragraph={{ rows: 4 }} />
                  </div>
                ) : (
                  menu
                )
              }
              notFoundContent={
                clustersLoading ? (
                  <div style={{ padding: 12 }}>
                    <Skeleton active title={false} paragraph={{ rows: 3 }} />
                  </div>
                ) : (
                  "No clusters found"
                )
              }
            >
              {clusterOptions.map((cluster) => (
                <Select.OptGroup key={cluster.name} label={cluster.name}>
                  {cluster.sites.map((site) => (
                    <Option
                      key={`${cluster.name}::${site}`}
                      value={`${cluster.name}::${site}`}
                    >
                      {site}
                    </Option>
                  ))}
                </Select.OptGroup>
              ))}
            </Select>
          </Form.Item>

          <div style={{ textAlign: "right" }}>
            <Space>
              <Button onClick={onCancel}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={creating || updating}
              >
                {mode === "create" ? "Create Role" : "Save Changes"}
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </>
  );
};

export default RoleModal;
