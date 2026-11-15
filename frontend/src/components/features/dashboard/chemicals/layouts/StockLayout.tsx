"use client";
import React, { memo } from "react";
import { SimpleStockProvider, useSimpleStock } from "../context/StockContext";
import StockCards from "../components/cards/StockCards";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/stockLayout.module.css";

const SimpleStockLayoutContent: React.FC = memo(() => {
  const { selectedCluster, selectedPlant } = useSimpleStock();

  const displayName =
    selectedPlant && selectedPlant !== "All Plants"
      ? getSiteDisplayName(selectedPlant)
      : selectedCluster && selectedCluster !== "All Clusters"
        ? selectedCluster
        : "Chemical Stock";

  return (
    <>
      <style jsx global>{`
        body {
          overflow-x: hidden !important;
          margin: 0;
          padding: 0;
        }
        html {
          overflow-x: hidden !important;
        }
      `}</style>
      <div className={cn("relative", layoutStyles.mainContainer)}>
        {/* Status Bar */}
        <CompactStatusBar
          activeTab="all"
          onTabChange={() => {}}
          siteName={displayName}
          dateRangeText=""
          customTabs={[]}
          showFilters={false}
        />

        {/* Main Content */}
        <div className={layoutStyles.contentContainer}>
          <div className={layoutStyles.cardsWrapper}>
            <StockCards />
          </div>
        </div>
      </div>
    </>
  );
});

SimpleStockLayoutContent.displayName = "SimpleStockLayoutContent";

const SimpleStockLayout: React.FC = () => (
  <SimpleStockProvider>
    <SimpleStockLayoutContent />
  </SimpleStockProvider>
);

export default SimpleStockLayout;
