import React, { memo } from "react";
import { Skeleton } from "antd";

import { AnalysisTemplateContext } from "../../context/AnalysisTemplateContext";

import { useContextSelector } from "use-context-selector";
import ErrorState from "../../../../../common/ErrorState";
import Select from "../../../../../common/widgets/Select";

const SitesList = () => {
  const selectedSite = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.selectedSite
  );

  const sites = useContextSelector(AnalysisTemplateContext, (v) => v.sites);

  const isFetchingSites = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.isFetchingSites
  );

  const sitesError = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.sitesError
  );

  const handleSelectSite = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSelectSite
  );

  if (sitesError) {
    return <ErrorState className="h-[10vh]" />;
  }

  if (isFetchingSites) {
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
    <Select
      value={selectedSite || undefined}
      displayKey="displayName"
      valueKey="name"
      placeholder="Select Site"
      style={{ width: 200 }}
      options={sites}
      onChange={(value) => handleSelectSite(value as string)}
    />
  );
};

const SiteSection = () => {
  return (
    <div className="bg-bg-container dark:bg-bg-elevated rounded-md px-6 py-16">
      <p className="text-text-base dark:text-text-heading mx-12 text-sm font-semibold">
        Sites
      </p>
      <div className="mx-12 mt-8">
        <SitesList />
      </div>
    </div>
  );
};

export default memo(SiteSection);
