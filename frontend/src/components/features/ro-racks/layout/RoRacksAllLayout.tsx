"use client";

import React, { useState, useMemo } from "react";
import { Button } from "antd";
import RoRacksChart from "@/components/features/ro-racks/components/charts/RoRacksChart";
import RoQualityCards from "@/components/features/ro-racks/components/cards/RoQualityCards";
import RoQualityCardsUAQ from "@/components/features/ro-racks/components/cards/RoQualityCardsUAQ";
import RoRacksOverviewTable from "@/components/features/ro-racks/components/table/rorackstable";
import RoOperationalStatusTable from "@/components/features/ro-racks/components/table/RoOperationalStatusTable";
import { useGetRoRacksDataQuery } from "@/store/api/roRacksApi";
import { useRoRacksContext } from "@/components/features/ro-racks/context/RoRacksContext";
import {
  arrayToCardObject,
  getChartData,
  CardItem,
} from "@/components/features/ro-racks/utils/roRacksUtils";
import { ColumnData } from "@/types/analysis.types";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";

interface ApiCardItem {
  columnName: string;
  dataSource?: (number | string)[];
  percent?: number;
}

const RoRacksAllLayout = () => {
  const [activeTab, setActiveTab] = useState<"firstPass" | "secondPass">(
    "firstPass"
  );
  const { selectedFilters, selectedSite, isLoadingOverall } =
    useRoRacksContext();

  const site_name = selectedSite || selectedFilters?.plant; // Use global site first
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");
  const isUAQ = site_name === "Umm Al Quwain IWP";

  // --- Fetch Data ---
  const { data, isLoading, error } = useGetRoRacksDataQuery(
    { site_name, selectedDate, pass: activeTab },
    {
      selectFromResult: ({ data, isFetching, isLoading, error }) => ({
        data,
        isLoading: isFetching || isLoading,
        error,
      }),
      skip: !site_name || !selectedDate,
    }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "ro_racks_graph",
        name: "RO Racks Graph",
        data_availability_for_given_date:
          data?.data.data_availability_for_given_date,
        from_date: data?.data.from_date,
        to_date: data?.data.to_date,
        isLoading: isLoading,
        isFetching: isLoading,
      },
    ],
    [
      data?.data.data_availability_for_given_date,
      data?.data.from_date,
      data?.data.to_date,
      isLoading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  // --- Extract All Cards ---
  const allCards = useMemo<ApiCardItem[]>(
    () => (Array.isArray(data?.data?.cards) ? data.data.cards : []),
    [data]
  );

  const passPrefix = activeTab === "firstPass" ? "Pass 1" : "Pass 2";
  const streamList = ["Stream1", "Stream2", "Stream3"];

  // --- Quality Cards Filtering ---
  const roQualityCardNames = isUAQ
    ? streamList.flatMap((stream) =>
        activeTab === "firstPass"
          ? [
              `${stream} RO Inlet Temperature`,
              `${stream} RO Inlet Conductivity`,
              `${stream} Conductivity`,
            ]
          : [
              `${stream} RO Inlet Temperature`,
              `${stream} RO Inlet Conductivity`,
              `${stream} Ph`,
            ]
      )
    : activeTab === "firstPass"
      ? ["RO Inlet Temperature", "RO Inlet Conductivity", "Conductivity"]
      : ["RO Inlet Temperature", "RO Inlet Conductivity", "Ph"];

  // --- KPI (Chart Cards) Filtering ---
  const roChartCardNames = isUAQ
    ? streamList.flatMap((stream) => [
        `${stream} ${passPrefix} Permeate Flow`,
        `${stream} ${passPrefix} Permeate Flow Percent`,
        `${stream} ${passPrefix} SEC`,
        `${stream} ${passPrefix} SEC Percent`,
      ])
    : [
        `${passPrefix} Permeate Flow`,
        `${passPrefix} Permeate Flow Percent`,
        `${passPrefix} SEC`,
        `${passPrefix} SEC Percent`,
      ];

  // --- Convert to Card Object ---
  const qualityCardsObj: Record<string, CardItem> = useMemo(
    () =>
      arrayToCardObject(
        allCards.filter((item) => roQualityCardNames.includes(item.columnName))
      ),
    [allCards, roQualityCardNames]
  );

  const chartCardsObj: Record<string, CardItem> = useMemo(
    () =>
      arrayToCardObject(
        allCards.filter((item) => roChartCardNames.includes(item.columnName))
      ),
    [allCards, roChartCardNames]
  );

  // --- Chart Data ---
  const chartData: ColumnData[] = useMemo(() => getChartData(data), [data]);

  if (error)
    return (
      <p className="text-center text-red-500">Failed to load RO Racks data.</p>
    );

  // --- Render ---
  return (
    <div className="space-y-20 p-6">
      {/* Tabs */}
      <div className="flex w-full gap-4 rounded-2xl bg-white p-5 px-12">
        <Button
          type={activeTab === "firstPass" ? "primary" : "default"}
          size="large"
          onClick={() => setActiveTab("firstPass")}
        >
          1st Pass RO Racks
        </Button>
        <Button
          type={activeTab === "secondPass" ? "primary" : "default"}
          size="large"
          onClick={() => setActiveTab("secondPass")}
        >
          2nd Pass RO Racks
        </Button>
      </div>

      {/* Quality Cards */}
      {isUAQ ? (
        <RoQualityCardsUAQ
          pass={activeTab}
          cards={qualityCardsObj}
          loading={isLoadingOverall || isLoading}
        />
      ) : (
        <RoQualityCards
          pass={activeTab}
          cards={qualityCardsObj}
          loading={isLoadingOverall || isLoading}
        />
      )}

      {/* Chart + KPI Cards */}
      <RoRacksChart
        pass={activeTab}
        data={{ cards: chartCardsObj, chartData }}
        loading={isLoading}
      />

      {/* Tables */}
      <RoRacksOverviewTable pass={activeTab} />
      <RoOperationalStatusTable pass={activeTab} />
    </div>
  );
};

export default RoRacksAllLayout;
