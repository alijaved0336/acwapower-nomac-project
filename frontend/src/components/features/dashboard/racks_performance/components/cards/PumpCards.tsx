"use client";

import React, { FC, useMemo } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Alert, Skeleton, theme } from "antd";
import { useAppSelector } from "@/hooks";
import { usePumpPerformance } from "../../context/PumpPerformanceContext";
import { PUMP_CARD_CONFIG, MetricData } from "../../utils/pumpCardsConfig";
import * as S from "../../utils/pumpCardsStyles";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";

// Card colors configuration
const CARD_COLORS_LIGHT = [
  {
    bg: "from-blue-50 to-blue-100",
    text: "text-blue-900",
  },
  {
    bg: "from-cyan-50 to-cyan-100",
    text: "text-cyan-900",
  },
  {
    bg: "from-purple-50 to-purple-100",
    text: "text-purple-900",
  },
  {
    bg: "from-orange-50 to-orange-100",
    text: "text-orange-900",
  },
];

const CARD_COLORS_DARK = [
  {
    bg: "from-gray-800 to-gray-700",
    text: "text-blue-100",
  },
  {
    bg: "from-gray-800 to-gray-700",
    text: "text-cyan-100",
  },
  {
    bg: "from-gray-800 to-gray-700",
    text: "text-purple-100",
  },
  {
    bg: "from-gray-800 to-gray-700",
    text: "text-orange-100",
  },
];

const SingleMetricCard: FC<{ metric: MetricData; colorIndex: number }> = ({
  metric,
  colorIndex,
}) => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  const isEmptyValue = metric.value === null || isNaN(metric.value);
  const colors = isDark
    ? CARD_COLORS_DARK[colorIndex % CARD_COLORS_DARK.length]
    : CARD_COLORS_LIGHT[colorIndex % CARD_COLORS_LIGHT.length];

  return (
    <div
      className={`box-border flex max-w-full min-w-0 flex-row items-center justify-between gap-1.5 rounded-lg bg-gradient-to-r px-3 py-1.5 ${colors.bg}`}
      style={{
        border: `1px solid ${token.colorBorder}`,
        boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
      }}
    >
      <div className={`flex-shrink-0 text-sm font-medium ${colors.text}`}>
        <span className="truncate">{metric.label}</span>
      </div>

      <div className="flex min-w-0 flex-shrink-0 items-center gap-1.5">
        {metric.showTrend &&
          metric.trend !== "insufficient" &&
          metric.trend && (
            <>
              {metric.trend === "up" && !isEmptyValue && (
                <TrendingUp
                  className="h-5 w-5 flex-shrink-0 text-green-500"
                  style={{ strokeWidth: 2.5 }}
                />
              )}
              {metric.trend === "down" && !isEmptyValue && (
                <TrendingDown
                  className="h-5 w-5 flex-shrink-0 text-red-500"
                  style={{ strokeWidth: 2.5 }}
                />
              )}
            </>
          )}

        <div className="flex min-w-0 flex-shrink-0 items-baseline gap-0.5">
          <span
            className={`truncate text-lg leading-none font-semibold ${colors.text}`}
          >
            {isEmptyValue
              ? PUMP_CARD_CONFIG.FORMATTING.EMPTY_VALUE
              : Number(metric.value).toFixed(metric.decimalPlaces)}
          </span>
          <span
            className={`flex-shrink-0 text-[10px] font-normal opacity-70 ${colors.text}`}
          >
            {metric.unit}
          </span>
        </div>
      </div>
    </div>
  );
};

const PumpCards: FC = () => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const { cardsData, cardsLoading, isError, error } = usePumpPerformance();

  const apiConfigs = useMemo(
    () => [
      {
        key: "pump_cards",
        name: "Pump KPI Cards",
        data_availability_for_given_date:
          cardsData?.cards[0]?.modified === true ? false : true,
        from_date: cardsData?.cards[0]?.timestamp,
        to_date: "",
        isLoading: cardsLoading,
        isFetching: cardsLoading,
      },
    ],
    [cardsLoading, cardsData?.cards]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const processedCardsData = useMemo<MetricData[]>(() => {
    if (!cardsData?.cards || cardsData.cards.length === 0) {
      return PUMP_CARD_CONFIG.METRICS.map((config) => ({
        label: config.label,
        value: null,
        unit: config.unit,
        isModified: false,
        showTrend: config.showTrend,
        decimalPlaces: config.decimalPlaces,
      }));
    }

    const cardsMap = Object.fromEntries(
      cardsData.cards.map((item: { columnName: any }) => [
        item.columnName,
        item,
      ])
    );

    return PUMP_CARD_CONFIG.METRICS.map((config) => {
      const data = cardsMap[config.key];
      const tendencyData = cardsData.tendency?.columns[config.key];
      const tendencyValue = tendencyData?.tendency?.toUpperCase();

      let trend: "up" | "down" | "insufficient" | undefined;

      if (tendencyValue === "INSUFFICIENT_HISTORY") {
        trend = PUMP_CARD_CONFIG.TREND_TYPES.INSUFFICIENT;
      } else if (tendencyValue === "UP") {
        trend = PUMP_CARD_CONFIG.TREND_TYPES.UP;
      } else if (tendencyValue === "DOWN") {
        trend = PUMP_CARD_CONFIG.TREND_TYPES.DOWN;
      }

      return {
        label: config.label,
        value: data?.value ? Number(data.value) : null,
        unit: config.unit,
        isModified: data?.modified || false,
        trend,
        showTrend: config.showTrend,
        decimalPlaces: config.decimalPlaces,
      };
    });
  }, [cardsData]);

  if (isError) {
    return (
      <Alert
        message="Error loading pump metrics"
        description={error?.status || "An unexpected error occurred"}
        type="error"
        showIcon
      />
    );
  }

  if (cardsLoading) {
    return (
      <>
        {[0, 1, 2, 3].map((i) => {
          const colors = isDark ? CARD_COLORS_DARK[i] : CARD_COLORS_LIGHT[i];
          return (
            <div
              key={i}
              className={`flex min-w-0 items-center justify-between rounded-lg bg-gradient-to-r px-3 py-1.5 ${colors.bg}`}
              style={{
                border: `1px solid ${token.colorBorder}`,
                boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
              }}
            >
              <Skeleton.Input
                active
                className="w-[50px]"
                style={{ minWidth: "unset" }}
                size="small"
              />
              <Skeleton.Input
                active
                className="w-[70px]"
                style={{ minWidth: "unset" }}
                size="small"
              />
            </div>
          );
        })}
      </>
    );
  }

  return (
    <>
      {processedCardsData.slice(0, 4).map((metric, index) => (
        <SingleMetricCard key={index} metric={metric} colorIndex={index} />
      ))}
    </>
  );
};

export default PumpCards;
