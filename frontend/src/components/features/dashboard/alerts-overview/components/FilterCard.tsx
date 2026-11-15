"use client";

import React from "react";
import { Button, Spin } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

interface FilterCardProps {
  onReset?: () => void;
  children?: React.ReactNode;
  className?: string;
  inline?: boolean;
  loading?: boolean;
  title?: string;
}

const FilterCard: React.FC<FilterCardProps> = ({
  onReset,
  children,
  className = "",
  inline = false,
  loading = false,
  title,
}) => {
  // Shared container styles
  const baseStyles =
    "rounded-2xl border border-gray-200 bg-white shadow-sm transition-all duration-300";

  // Responsive padding: smaller on mobile
  const paddingStyles = "px-6 sm:px-12 py-8 sm:py-12";

  if (inline) {
    return (
      <div className={`${baseStyles} ${paddingStyles} ${className}`}>
        {/* Optional title */}
        {title && (
          <h3 className="mb-4 text-xl font-semibold text-gray-800">{title}</h3>
        )}

        {/* Filters & Reset */}
        <div className="flex w-full flex-wrap items-start justify-between gap-6 sm:gap-10">
          {/* Filters section */}
          <div className="flex flex-1 flex-wrap items-center gap-6 sm:gap-10">
            {loading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Spin size="small" /> <span>Loading...</span>
              </div>
            ) : (
              children
            )}
          </div>

          {/* Reset Button */}
          {onReset && (
            <Button
              type="text"
              danger
              icon={<ReloadOutlined />}
              onClick={onReset}
              className="mt-2 flex items-center gap-2 whitespace-nowrap sm:mt-4"
            >
              Reset Filter
            </Button>
          )}
        </div>
      </div>
    );
  }

  // Default sticky version
  return (
    <>
      <div className="h-12 sm:h-16" />
      <div
        className={`sticky top-0 z-10 ${baseStyles} ${paddingStyles} ${className}`}
      >
        {/* Optional title */}
        {title && (
          <h3 className="mb-4 text-xl font-semibold text-gray-800">{title}</h3>
        )}

        <div className="flex w-full flex-wrap items-start justify-between gap-6 sm:gap-10">
          {/* Filters */}
          <div className="flex flex-1 flex-wrap items-center gap-6 sm:gap-10">
            {loading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Spin size="small" /> <span>Loading...</span>
              </div>
            ) : (
              children
            )}
          </div>

          {/* Reset Button */}
          {onReset && (
            <Button
              type="text"
              danger
              icon={<ReloadOutlined />}
              onClick={onReset}
              className="mt-2 flex items-center gap-2 whitespace-nowrap sm:mt-4"
            >
              Reset Filter
            </Button>
          )}
        </div>
      </div>
    </>
  );
};

export default FilterCard;
