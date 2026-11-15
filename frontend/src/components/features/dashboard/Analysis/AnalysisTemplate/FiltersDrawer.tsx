import { Button, Divider, Drawer, Space } from "antd";
import React, { FC, memo } from "react";
import DateRangePicker from "../../../../common/widgets/DateRangePicker";
import RackSection from "./Sidebar/RackSection";
import { AnalysisTemplateContext } from "../context/AnalysisTemplateContext";
import { useContextSelector } from "use-context-selector";
import dayjs from "dayjs";
import { DateFormat } from "../../../../../constants/enums";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}
const FiltersDrawer: FC<FiltersDrawerProps> = ({ onClose, open }) => {
  const isFetchingWidgets = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingWidgets
  );

  const dateFilter = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.dateFilter
  );

  const handleDatesChange = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleDatesChange
  );

  const handleResetFilters = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleResetFilters
  );

  return (
    <div>
      <Drawer
        title="Filters"
        placement="right"
        onClose={onClose}
        open={open}
        width={360}
        extra={
          <Button onClick={handleResetFilters} size="small">
            Reset All
          </Button>
        }
      >
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          {/* Racks */}
          <div>
            <label
              style={{
                display: "block",
                marginBottom: 8,
                fontWeight: 500,
                fontSize: "14px",
              }}
            >
              Racks
            </label>
            <RackSection />
          </div>
        </Space>
      </Drawer>
    </div>
  );
};

export default memo(FiltersDrawer);
