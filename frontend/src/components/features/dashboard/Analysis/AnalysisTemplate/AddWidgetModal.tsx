import React, { memo } from "react";
import { Modal, Button } from "antd";
import { AnalysisTemplateContext } from "../context/AnalysisTemplateContext";
import { useContextSelector } from "use-context-selector";
import Heading from "../../../../common/typography/Heading";
import RadioCard from "../../../../common/widgets/RadioCard";
import { WIDGET_OPTIONS } from "../constants/constants";

const AddWidgetModal = () => {
  const isAddWidgetModalOpen = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isAddWidgetModalOpen
  );

  const selectedWidgetId = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedWidgetId
  );

  const handleAddNewWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleAddNewWidget
  );

  const handleSelectWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSelectWidget
  );

  const handleCloseAddWidgetModal = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleCloseAddWidgetModal
  );

  return (
    <Modal
      title={
        <Heading level={5} className="text-text-base font-bold">
          Add New Widget
        </Heading>
      }
      open={isAddWidgetModalOpen}
      onCancel={handleCloseAddWidgetModal}
      footer={null}
      width={500}
      centered
    >
      <div className="space-y-16">
        <div>
          <p className="text-text-secondary mt-1 text-sm">
            Select the type of widget you want to create.
          </p>
        </div>

        <div className="bg-bg-container rounded-md p-16">
          <div className="grid grid-cols-2 gap-12">
            {WIDGET_OPTIONS.map((option) => (
              <RadioCard
                key={option.id}
                value={option.id}
                checked={selectedWidgetId === option.id}
                onChange={(e) => handleSelectWidget(e.target.value)}
                className="!w-full"
              >
                {option.label}
              </RadioCard>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <Button
            variant="outlined"
            color="default"
            onClick={handleCloseAddWidgetModal}
          >
            Cancel
          </Button>
          <Button
            type="primary"
            onClick={handleAddNewWidget}
            disabled={!selectedWidgetId}
          >
            Add Chart
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default memo(AddWidgetModal);
