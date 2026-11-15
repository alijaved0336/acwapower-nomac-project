// src/components/features/dashboard/Analysis/AnalysisTemplate/Sidebar/AnalysisSelector.tsx
import React, { useState } from "react";
import { Analysis } from "../../../../../../types/analysis.types";
import { useAnalysisTemplate } from "../../context/AnalysisTemplateContext";
import { Input, Button } from "antd";
import Select from "../../../../../common/widgets/Select";

interface AnalysisSelectorProps {
  selectedAnalysisId: string | undefined;
  onAnalysisChange: (analysisId: string) => void;
  widgetId: string;
  analysisList: Analysis[];
  isAnalysisLoading: boolean;
  disabled?: boolean;
}

const AnalysisSelector: React.FC<AnalysisSelectorProps> = ({
  selectedAnalysisId,
  onAnalysisChange,
  widgetId,
  analysisList,
  isAnalysisLoading,
  disabled = false,
}) => {
  const { isCopyingWidget, handleCopyWidget } = useAnalysisTemplate();
  const [widgetName, setWidgetName] = useState("");

  const handleAnalysisChange = (analysisId: string) => {
    onAnalysisChange(analysisId);
  };

  const handleCopy = async () => {
    if (selectedAnalysisId) {
      await handleCopyWidget(widgetId, selectedAnalysisId, widgetName);
      setWidgetName("");
    }
  };

  return (
    <div className="flex gap-3 space-y-3">
      <div className="gap w-50">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Widget Name (Optional)
        </label>
        <div className="w-50">
          <Input
            value={widgetName}
            onChange={(e) => setWidgetName(e.target.value)}
            placeholder="Enter widget name"
            disabled={disabled || isCopyingWidget}
            size="large"
          />
        </div>
      </div>
      <div className="gap w-50">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Select Analysis
        </label>
        <div className="flex items-center gap-3">
          <div className="w-50">
            <Select<Analysis>
              value={selectedAnalysisId?.toString() || undefined}
              placeholder="Choose an Analysis"
              onChange={(value) => handleAnalysisChange(value)}
              options={analysisList}
              displayKey="name"
              valueKey="id"
              loading={isAnalysisLoading}
              notFoundContent="No analysis templates found"
            />
          </div>
          <Button
            type="primary"
            onClick={handleCopy}
            loading={isCopyingWidget}
            disabled={!selectedAnalysisId || disabled}
            className="h-10 px-6"
          >
            Copy
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AnalysisSelector;
