import React, { useState, useEffect } from "react";
import { Alert } from "antd";
import {
  pumpTabsContainerStyle,
  tabsWrapperStyle,
  getTabButtonStyleNoBorder,
  getTabHoverStyleNoBorder,
  getTabLeaveStyleNoBorder,
  PUMP_TABS_CSS_CLASS,
  injectPumpTabsStyles,
} from "../../utils/pumpTabsStyles";

interface Tab {
  id: string;
  label: string;
}

interface PumpTypeTabsProps {
  title: string;
  fetchTabs: () => Promise<Tab[]>;
  onTabChange?: (categoryId: string) => void;
  activeTabKey?: string;
}

const PumpTypeTabs: React.FC<PumpTypeTabsProps> = ({
  fetchTabs,
  onTabChange,
  activeTabKey,
}) => {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activeTab, setActiveTab] = useState<string>(activeTabKey || "");
  const [error, setError] = useState<string | null>(null);
  const initialTabSetRef = React.useRef(false);

  useEffect(() => {
    injectPumpTabsStyles();
  }, []);

  useEffect(() => {
    if (activeTabKey && activeTabKey !== activeTab) {
      setActiveTab(activeTabKey);
    }
  }, [activeTabKey, activeTab]);

  useEffect(() => {
    const loadTabs = async () => {
      try {
        setError(null);
        const data = await fetchTabs();

        if (Array.isArray(data) && data.length > 0) {
          setTabs(data);

          if (activeTabKey) {
            setActiveTab(activeTabKey);
            initialTabSetRef.current = true;
          } else if (!initialTabSetRef.current) {
            const firstTab = data[0]?.id;
            if (firstTab) {
              setActiveTab(firstTab);
              if (onTabChange) {
                onTabChange(firstTab);
                initialTabSetRef.current = true;
              }
            }
          }
        }
      } catch (err) {
        setError("Failed to load pump categories");
        console.error("Error loading tabs:", err);
      }
    };
    loadTabs();
  }, [fetchTabs, onTabChange, activeTabKey]);

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId);
    if (onTabChange) {
      onTabChange(tabId);
    }
  };

  if (error) {
    return (
      <div style={pumpTabsContainerStyle}>
        <Alert
          message="Error loading pump categories"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  if (tabs.length === 0) {
    return null;
  }

  return (
    <div style={pumpTabsContainerStyle}>
      <div style={tabsWrapperStyle} className={PUMP_TABS_CSS_CLASS}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              style={getTabButtonStyleNoBorder(isActive, false, false)}
              onMouseEnter={(e) => {
                Object.assign(
                  e.currentTarget.style,
                  getTabHoverStyleNoBorder(isActive)
                );
              }}
              onMouseLeave={(e) => {
                Object.assign(
                  e.currentTarget.style,
                  getTabLeaveStyleNoBorder(isActive)
                );
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default PumpTypeTabs;
