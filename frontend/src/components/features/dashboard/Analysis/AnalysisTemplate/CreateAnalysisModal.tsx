"use client";
import React from "react";
import { Modal, Form, Input, Select, Button } from "antd";
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCreateAnalysisMutation } from "@/store/api/analysisApi";
import type { CreateAnalysisPayload } from "@/types/analysis.types";
import { useRouter } from "next/navigation";
import { useAppSelector } from "../../../../../hooks";

type Props = {
  open: boolean;
  onClose: () => void;
  defaultValues?: Partial<CreateAnalysisPayload>;
};

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  visibility: z.enum(["public", "private"], {
    required_error: "Visibility is required",
  }),
});

type FormValues = z.infer<typeof schema>;

const CreateAnalysisModal: React.FC<Props> = ({
  open,
  onClose,
  defaultValues,
}) => {
  const router = useRouter();
  const [createAnalysis, { isLoading }] = useCreateAnalysisMutation();
  const user = useAppSelector((state) => state.auth.user);

  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: defaultValues?.name ?? "",
      visibility:
        (defaultValues?.visibility as "public" | "private") ?? "private",
    },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const payload: CreateAnalysisPayload = {
        user_id: user?.id || "unknown",
        name: values.name,
        asset_type: "asasa",
        type: "SWRO Plant",
        visibility: values.visibility,
      };

      const res = await createAnalysis(payload).unwrap();
      if (res?.id) {
        reset();
        onClose();
        router.push(`/dashboard/analysis/${res.id}`);
      }
    } catch (error) {
      console.error("Error creating analysis:", error);
    }
  };

  const handleCancel = () => {
    reset();
    onClose();
  };

  return (
    <Modal
      title={
        <span className="text-base font-semibold text-black dark:text-white">
          Create Analysis
        </span>
      }
      open={open}
      onCancel={handleCancel}
      footer={null}
      destroyOnHidden
      maskClosable={!isLoading}
      className="!top-20"
      centered
    >
      <Form layout="vertical" onFinish={handleSubmit(onSubmit)}>
        <Form.Item
          label="Name"
          validateStatus={errors.name ? "error" : ""}
          help={errors.name?.message}
        >
          <Controller
            control={control}
            name="name"
            render={({ field }) => (
              <Input
                {...field}
                placeholder="Enter analysis name"
                disabled={isLoading}
              />
            )}
          />
        </Form.Item>

        <Form.Item
          label="Visibility"
          validateStatus={errors.visibility ? "error" : ""}
          help={errors.visibility?.message}
        >
          <Controller
            control={control}
            name="visibility"
            render={({ field }) => (
              <Select
                {...field}
                options={[
                  { label: "Private", value: "private" },
                  { label: "Public", value: "public" },
                ]}
                disabled={isLoading}
                className="!w-full"
              />
            )}
          />
        </Form.Item>

        <div className="flex justify-end gap-3">
          <Button onClick={handleCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="primary" htmlType="submit" loading={isLoading}>
            Create
          </Button>
        </div>
      </Form>
    </Modal>
  );
};

export default CreateAnalysisModal;
