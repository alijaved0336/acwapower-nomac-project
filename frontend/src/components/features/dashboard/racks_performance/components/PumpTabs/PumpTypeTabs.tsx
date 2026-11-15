"use client";

import React, { FC } from "react";
import { Spin, Alert } from "antd";
import { usePumpPerformance } from "../../context/PumpPerformanceContext";
import {
  pumpTabsContainerStyle,
  tabsTitleStyle,
  tabsWrapperStyle,
  getTabButtonStyle,
  getTabHoverStyle,
  getTabLeaveStyle,
} from "../../utils/pumpTabsStyles";

interface PumpTypeTabsProps {
  title: string;
}

const PumpTypeTabs: FC<PumpTypeTabsProps> = ({ title }) => {
  const {
    pumpCategories,
    activeTab,
    setActiveTab,
    setSelectedCategory,
    isError,
    error,
  } = usePumpPerformance();

  const handleTabClick = (categoryId: string) => {
    console.log("Tab clicked:", categoryId);
    setActiveTab(categoryId);
    setSelectedCategory(categoryId);
  };

  if (isError) {
    return (
      <div style={pumpTabsContainerStyle}>
        <Alert
          message="Error loading pump categories"
          description={
            error?.status
              ? `Failed to fetch data: ${error.status}`
              : "An unexpected error occurred"
          }
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={pumpTabsContainerStyle}>
      {/* <div style={tabsTitleStyle}>{title}</div> */}
      <div style={tabsWrapperStyle}>
        {pumpCategories.length === 0 ? (
          <Spin size="small" />
        ) : (
          pumpCategories.map((category, index) => {
            const isActive = activeTab === category.id;
            const isFirst = index === 0;
            const isLast = index === pumpCategories.length - 1;

            return (
              <button
                key={category.id}
                onClick={() => handleTabClick(category.id)}
                style={getTabButtonStyle(isActive, isFirst, isLast)}
                onMouseEnter={(e) =>
                  Object.assign(
                    e.currentTarget.style,
                    getTabHoverStyle(isActive)
                  )
                }
                onMouseLeave={(e) =>
                  Object.assign(
                    e.currentTarget.style,
                    getTabLeaveStyle(isActive)
                  )
                }
              >
                {category.name}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};

export default PumpTypeTabs;
