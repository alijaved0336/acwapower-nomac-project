"use client";

import { Card, Skeleton } from "antd";
import { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon?: ReactNode;
  loading?: boolean;
}

export default function MetricCard({
  title,
  value,
  unit,
  icon,
  loading,
}: Readonly<MetricCardProps>) {
  return (
    <Card
      style={{ height: "100%" }}
      styles={{
        body: { padding: "0.5rem", height: "100%" },
      }}
    >
      <div className="flex h-full flex-col justify-between gap-16">
        <div className="flex items-center justify-between gap-3">
          {/* Left Content */}
          <div className="spacey-8 grow">
            {/* Title */}
            <div className="mb-2 text-base font-medium dark:text-white/70">
              {title}
            </div>

            {/* Value and Previous Value */}
            <div className="flex items-baseline gap-2">
              {loading ? (
                <Skeleton.Input
                  size="small"
                  active
                  style={{ minWidth: "4rem", width: "4rem", height: "1rem" }}
                />
              ) : (
                <>
                  {unit && (
                    <span className="text-xs dark:text-white/50">{unit}</span>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Right Icon */}
          {icon && <div>{icon}</div>}
        </div>
        <div className="flex items-baseline gap-8">
          {loading ? (
            <Skeleton.Input size="small" active style={{ height: "1rem" }} />
          ) : (
            <span className="text-xl font-bold dark:text-white">{value}</span>
          )}
          {/* <span className="text-xs font-bold dark:text-white/50">Actual</span> */}
        </div>
      </div>
    </Card>
  );
}
