"use client";

import { Button, Select, Skeleton } from "antd";
import React, { memo } from "react";
import { BackIcon, SaveIcon } from "../../../../../assets/icons";
import { DownOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { AnalysisTemplateContext } from "../context/AnalysisTemplateContext";

import { useContextSelector } from "use-context-selector";

import TitleInput from "./TitleInput";

import Header from "../../../../layouts/DashboardLayout/Header";

import { ProfileSection } from "../../../../common/CompactStatusBar";

const AnalysisTemplateHeader = () => {
  const router = useRouter();
  const widgets = useContextSelector(AnalysisTemplateContext, (v) => v.widgets);

  const analysisName = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.analysisName
  );

  const visibility = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.visibility
  );

  const isSavingWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isSavingWidgets
  );

  const isFetchingWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingWidgets
  );

  const dateFilter = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.dateFilter
  );

  const handleChangeAnalysisName = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleChangeAnalysisName
  );

  const handleChangeVisibility = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleChangeVisibility
  );

  const handleDatesChange = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleDatesChange
  );

  const handleSaveWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSaveWidgets
  );

  const handleResetFilters = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleResetFilters
  );

  const handleOpenAddWidgetModal = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleOpenAddWidgetModal
  );

  // Check if we're opening an existing analysis (not creating a new one)
  const isSaving = isSavingWidgets;

  return (
    <Header>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-16">
          <Button
            icon={<BackIcon width={14} height={14} />}
            type="text"
            className="flex !h-8 !w-8 !min-w-8 items-center justify-center rounded-md !border-0 !p-0 hover:!bg-gray-100"
            onClick={() => router.back()}
          />

          <div>
            <div className="mb-1 flex items-center gap-8">
              {isFetchingWidgets ? (
                <Skeleton.Input active block size="small" />
              ) : (
                <TitleInput
                  className="dark:text-text-heading !m-0 !border-0 !p-0 text-base font-bold text-black !shadow-none"
                  value={analysisName}
                  onChange={(value: string) => handleChangeAnalysisName(value)}
                />
              )}
            </div>
            <div className="dark:text-text-heading flex items-center text-sm text-gray-900">
              <span className="text-sm leading-8">New Analysis</span>
              <Button
                type="text"
                className="ml-2 !h-auto !w-auto !border-0 !p-0 !shadow-none hover:!bg-transparent"
                size="small"
              />
            </div>
          </div>

          <Select
            value={visibility}
            onChange={handleChangeVisibility}
            className="!border-gray-300"
            style={{ minWidth: "100px" }}
            min-
            size="middle"
            suffixIcon={<DownOutlined />}
            options={[
              { value: "public", label: "Public" },
              { value: "private", label: "Private" },
            ]}
          />
        </div>

        <div className="flex items-center gap-8">
          {widgets.length > 0 && (
            <Button type="primary" onClick={handleOpenAddWidgetModal}>
              Add Widget
            </Button>
          )}

          <Button
            size="middle"
            className="!w-auto"
            type="primary"
            loading={isSaving}
            disabled={isSaving}
            onClick={handleSaveWidgets}
          >
            <SaveIcon /> Save
          </Button>
          {/* <FiltersDrawer open={isOpen} onClose={() => setIsOpen(false)} /> */}
          <ProfileSection />
        </div>
      </div>
    </Header>
  );
};

AnalysisTemplateHeader.displayName = "AnalysisTemplateHeader";

export default memo(AnalysisTemplateHeader);
