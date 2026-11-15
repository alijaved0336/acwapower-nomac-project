"use client";

import React from "react";
import { Button } from "antd";

interface FilterCardProps {
  onReset?: () => void;
  children?: React.ReactNode;
  className?: string;
  inline?: boolean;
}

const FilterCard: React.FC<FilterCardProps> = ({
  onReset,
  children,
  className = "",
  inline = false,
}) => {
  if (inline) {
    return (
      <div
        className={`rounded-lg border border-gray-200 bg-white px-12 py-16 shadow-sm dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 ${className}`}
      >
        {/* Filters and reset button on same row */}
        <div className="flex w-full flex-wrap items-start justify-between gap-12">
          {/* Filters */}
          <div className="flex flex-1 flex-wrap items-center gap-12">
            {children}
          </div>

          {/* Reset Filter button slightly lower */}
          {onReset && (
            <Button
              type="text"
              danger
              onClick={onReset}
              className="mt-4 flex items-center gap-4 whitespace-nowrap dark:text-slate-100" // 👈 Added margin-top
            >
              Reset Filter
            </Button>
          )}
        </div>
      </div>
    );
  }

  // Default stacked layout
  return (
    <>
      <div className="h-16"></div>
      <div
        className={`sticky top-0 z-10 mt-12 mb-16 rounded-lg border border-gray-200 bg-white px-24 py-16 shadow-sm dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 ${className}`}
      >
        {/* Filters and reset button on same row */}
        <div className="flex w-full flex-wrap items-start justify-between gap-12">
          {/* Filters */}
          <div className="flex flex-1 flex-wrap items-center gap-12">
            {children}
          </div>

          {/* Reset Filter button slightly lower */}
          {onReset && (
            <Button
              type="text"
              danger
              onClick={onReset}
              className="mt-4 flex items-center gap-4 whitespace-nowrap dark:text-slate-100" // 👈 Added margin-top
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
