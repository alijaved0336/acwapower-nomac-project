import React, { memo } from "react";
import Select from "../../../../common/widgets/Select";
import { WIDGET_OPTIONS } from "../constants/constants";
import { Button, Card } from "antd";
import { AnalysisTemplateContext } from "../context/AnalysisTemplateContext";
import Heading from "../../../../common/typography/Heading";
import RadioCard from "../../../../common/widgets/RadioCard";
import { useContextSelector } from "use-context-selector";

const AddNewWidget = () => {
  const widgets = useContextSelector(AnalysisTemplateContext, (v) => v.widgets);

  const isFetchingWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingWidgets
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

  // Do not show addd widget view while fetching widgtes
  if (isFetchingWidgets) return null;

  // Show card when no widgets exist, show dropdown when widgets exist
  if (widgets.length === 0) {
    return (
      <div className="mt-32 flex h-[5ovh] items-center justify-center">
        <Card className="min-w-[440px]">
          <div className="!space-y-16">
            <div>
              <Heading level={5} className="text-text-base font-semibold">
                Select Chart Type
              </Heading>

              <p className="text-text-secondary mt-1 text-sm">
                Select the type of chart you want to create.
              </p>
            </div>
            <div className="dark:bg-bg-container rounded-md p-16">
              <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,10rem),1fr))] gap-16">
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
            <Button
              className="block w-full"
              variant="solid"
              color="primary"
              size="large"
              onClick={handleAddNewWidget}
              disabled={!selectedWidgetId}
            >
              Add Chart
            </Button>
            {/* <p className="before:bg-border after:bg-border flex items-center gap-16 text-sm before:h-[1px] before:grow before:content-[''] after:h-[1px] after:grow after:content-['']">
              Or
            </p> */}
          </div>
        </Card>
      </div>
    );
  }
};

export default memo(AddNewWidget);
