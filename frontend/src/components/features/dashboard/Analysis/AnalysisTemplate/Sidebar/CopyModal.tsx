import React, { memo, useMemo, useState } from "react";
import { Modal, Button, Input } from "antd";
import {
  AnalysisTemplateContext,
  useAnalysisTemplate,
} from "../../context/AnalysisTemplateContext";
import Select from "../../../../../common/widgets/Select";
import { Analysis } from "../../../../../../types/analysis.types";
import { useAppSelector } from "../../../../../../hooks";
import { useGetAllAnalysisQuery } from "../../../../../../store/api/analysisApi";
import { useContextSelector } from "use-context-selector";

type CopyModalProps = {
  open: boolean;
  widgetId: string;
  onCancel: () => void;
  onSuccess?: () => void;
};

const CopyModal: React.FC<CopyModalProps> = ({
  open,
  widgetId,
  onCancel,
  onSuccess,
}) => {
  // Get analysis list and copy functionality from context
  const {
    data: analysisData,
    isLoading: isAnalysisLoading,
    error: analysisError,
  } = useGetAllAnalysisQuery({
    page: 1,
    limit: 100,
  });

  const analysisList = analysisData?.items || [];

  const isCopyingWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isCopyingWidget
  );

  const handleCopyWidget = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleCopyWidget
  );

  const user = useAppSelector((state) => state.auth.user);
  // Get current user ID

  // Filter analysis list by current user ID
  const filteredAnalysisList = useMemo(() => {
    if (!user?.id) return analysisList;
    return analysisList.filter((analysis) => {
      if ("user_id" in analysis && analysis.user_id) {
        return analysis.user_id === user.id;
      }
      return true;
    });
  }, [analysisList, user]);

  // Analysis selection state
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<
    string | undefined
  >(undefined);
  const [widgetName, setWidgetName] = useState("");

  const handleAnalysisChange = (analysisId: string) => {
    setSelectedAnalysisId(analysisId);
  };

  const handleCopy = async () => {
    if (selectedAnalysisId) {
      await handleCopyWidget(widgetId, selectedAnalysisId, widgetName);
      setWidgetName("");
      setSelectedAnalysisId(undefined);
      onSuccess?.();
    }
  };

  const handleCancel = () => {
    setSelectedAnalysisId(undefined);
    setWidgetName("");
    onCancel();
  };

  return (
    <Modal
      title="Copy Widget to Analysis"
      open={open}
      onCancel={handleCancel}
      footer={null}
      width={600}
      centered
    >
      <div className="space-y-6">
        <div className="flex gap-3 space-y-3">
          <div className="gap w-50">
            <label className="dark:text-text-heading mb-2 block text-sm font-medium text-gray-700">
              Widget Name (Optional)
            </label>
            <div className="w-50">
              <Input
                value={widgetName}
                onChange={(e) => setWidgetName(e.target.value)}
                placeholder="Enter widget name"
                disabled={isCopyingWidget}
                size="large"
              />
            </div>
          </div>
          <div className="gap w-50">
            <label className="dark:text-text-heading mb-2 block text-sm font-medium text-gray-700">
              Select Analysis
            </label>
            <div className="flex items-center gap-3">
              <div className="w-50">
                <Select<Analysis>
                  value={selectedAnalysisId?.toString() || undefined}
                  placeholder="Choose an Analysis"
                  onChange={(value) => handleAnalysisChange(value)}
                  options={filteredAnalysisList}
                  displayKey="name"
                  valueKey="id"
                  loading={isAnalysisLoading}
                  notFoundContent="No analysis templates found"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-8">
        <Button onClick={handleCancel}>Cancel</Button>
        <Button
          type="primary"
          onClick={handleCopy}
          loading={isCopyingWidget}
          disabled={!selectedAnalysisId}
        >
          Copy Widget
        </Button>
      </div>
    </Modal>
  );
};

export default memo(CopyModal);
