import React, { memo } from "react";
import { Skeleton } from "antd";

import { AnalysisTemplateContext } from "../../context/AnalysisTemplateContext";

import { useContextSelector } from "use-context-selector";
import ErrorState from "../../../../../common/ErrorState";
import MultiSelect from "../../../../../common/widgets/MultiSelect";
import { getTableDisplayName } from "../../../../../../utils/siteDisplayNames";

const TableList = () => {
  const selectedSite = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedSite
  );

  const tables = useContextSelector(AnalysisTemplateContext, (v) => v.tables);

  const isFetchingTables = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingTables
  );

  const tablesError = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.tablesError
  );

  const selectedTables = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedTables
  );

  const handleSelectTables = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSelectTables
  );

  if (tablesError) {
    return <ErrorState className="h-[10vh]" />;
  }

  if (isFetchingTables) {
    return (
      <div className="space-y-3">
        <Skeleton.Input
          active
          block
          size="default"
          style={{
            width: "100%",
            minWidth: "unset",
            maxWidth: "100%",
            boxSizing: "border-box",
          }}
        />
      </div>
    );
  }

  return (
    <MultiSelect
      value={(selectedTables || []).map((t) => `${t.siteName}:${t.tableName}`)}
      getLabel={(t) => getTableDisplayName(t.tableName)}
      getValue={(t) => `${t.siteName}:${t.tableName}`}
      placeholder="Select Tables"
      style={{ width: 200 }}
      options={tables}
      clear
      onClearAll={() => handleSelectTables([])}
      returnObject
      onChange={(items) => handleSelectTables(items as typeof tables)}
      maxTagCount={1}
      maxTagPlaceholder={(omitted) => `+${omitted.length} more`}
      listHeight={256}
    />
  );
};
const TableSection = () => {
  return (
    <div className="bg-bg-container dark:bg-bg-elevated rounded-md px-6 py-16">
      <p className="text-text-base dark:text-text-heading mx-12 text-sm font-semibold">
        Tables
      </p>
      <div className="mx-12 mt-8">
        <TableList />
      </div>
    </div>
  );
};

export default memo(TableSection);
