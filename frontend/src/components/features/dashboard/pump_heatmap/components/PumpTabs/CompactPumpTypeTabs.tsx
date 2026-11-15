"use client";

import React, { useState, useEffect } from "react";
import { Alert } from "antd";
import { DESIGN_SYSTEM } from "@/constants/designSystem";

interface Tab {
  id: string;
  label: string;
}

interface CompactPumpTypeTabsProps {
  title: string;
  fetchTabs: () => Promise<Tab[]>;
  onTabChange?: (categoryId: string) => void;
  activeTabKey?: string;
}

const CompactPumpTypeTabs: React.FC<CompactPumpTypeTabsProps> = ({
  fetchTabs,
  onTabChange,
  activeTabKey,
}) => {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activeTab, setActiveTab] = useState<string>(activeTabKey || "");
  const [error, setError] = useState<string | null>(null);
  const initialTabSetRef = React.useRef(false);

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
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
        style={{ margin: "8px" }}
      />
    );
  }

  if (tabs.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "4px",
        height: "100%",
        width: "100%",
        overflowX: "auto",
        overflowY: "hidden",
        scrollbarWidth: "none", // Firefox
        msOverflowStyle: "none", // IE and Edge
        WebkitOverflowScrolling: "touch", // Smooth scrolling on iOS
      }}
      className="compact-pump-tabs-container"
    >
      {tabs.map((tab, index) => {
        const isActive = activeTab === tab.id;

        // Rotate through colors for variety
        const colorSchemes = [
          {
            bg: DESIGN_SYSTEM.colors.accent.cyan,
            light: DESIGN_SYSTEM.colors.accent.cyanLight,
          },
          {
            bg: DESIGN_SYSTEM.colors.accent.purple,
            light: DESIGN_SYSTEM.colors.accent.purpleLight,
          },
          {
            bg: DESIGN_SYSTEM.colors.accent.orange,
            light: DESIGN_SYSTEM.colors.accent.orangeLight,
          },
          {
            bg: DESIGN_SYSTEM.colors.secondary.green,
            light: DESIGN_SYSTEM.colors.secondary.greenLight,
          },
        ];

        const colorScheme = colorSchemes[index % colorSchemes.length];

        return (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            style={{
              padding: "6px 12px",
              background: isActive
                ? `linear-gradient(135deg, ${colorScheme.bg} 0%, ${colorScheme.bg}dd 100%)`
                : colorScheme.light,
              color: isActive ? "white" : colorScheme.bg,
              border: `1px solid ${isActive ? colorScheme.bg : `${colorScheme.bg}33`}`,
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: isActive ? 700 : 600,
              cursor: "pointer",
              transition: "all 0.2s ease",
              letterSpacing: "0.3px",
              textTransform: "uppercase",
              boxShadow: isActive
                ? `0 2px 6px ${colorScheme.bg}40`
                : "0 1px 2px rgba(0, 0, 0, 0.05)",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = `${colorScheme.bg}20`;
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.boxShadow = `0 3px 8px ${colorScheme.bg}30`;
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = colorScheme.light;
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow =
                  "0 1px 2px rgba(0, 0, 0, 0.05)";
              }
            }}
          >
            {tab.label}
          </button>
        );
      })}

      {/* CSS to hide scrollbar */}
      <style jsx>{`
        .compact-pump-tabs-container::-webkit-scrollbar {
          display: none; /* Chrome, Safari, Opera */
        }
      `}</style>
    </div>
  );
};

export default CompactPumpTypeTabs;
