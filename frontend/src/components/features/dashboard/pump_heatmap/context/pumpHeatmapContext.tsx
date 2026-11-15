"use client";
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  ReactNode,
  useRef,
  useCallback,
} from "react";
import dayjs, { Dayjs } from "dayjs";
import {
  useGetPumpCategoriesQuery,
  useGetPumpHeatmapDataQuery,
} from "@/store/api/heatMapPumpApi";
import { usePersistedState } from "@/hooks";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { SiteId } from "../utils/pumpPerformanceData";
import { DateRangePickerType } from "@/types/common.types";
import { possibleDateColumnTypes } from "../../../../../constants/states";

interface PumpHeatmapFilters {
  from_date: string;
  to_date: string;
  category: string;
}

interface PumpHeatmapContextType {
  dateRange: [Dayjs, Dayjs];
  selectedCategory: string;
  pumpCategories: any[];
  heatmapData: any;
  heatmapError: any;
  handleDateRangeChange: (dates: DateRangePickerType) => void;
  handleTabChange: (categoryId: string) => void;
  chartTitle: string;
  processedHeatmapData: any[];
  chartHeight: number;
  showOverlaySpinner: boolean;
  isInitialLoading: boolean;
  initialDateSet: boolean;
  heatmapLoading: boolean;
  heatmapFetching: boolean;
  siteId: SiteId;
}

interface PumpHeatmapProviderProps {
  children: ReactNode;
  siteId: SiteId;
  title: string;
}

const PumpHeatmapContext = createContext<PumpHeatmapContextType | undefined>(
  undefined
);

export const PumpHeatmapProvider: React.FC<PumpHeatmapProviderProps> = ({
  children,
  siteId,
  title,
}) => {
  const hasLoadedOnce = useRef(false);
  const isSettingFromAPI = useRef(false);
  const [initialDateSet, setInitialDateSet] = useState(false);

  // URL-synced filters for better UX and shareability
  const {
    filters,
    setFilter,
    setFilters: setUrlFilters,
    isReady: urlFiltersReady,
  } = useUrlFilters<PumpHeatmapFilters>({
    filterConfig: {
      from_date: {
        serialize: (v: string) => v || null,
        deserialize: (v: string) => v,
        defaultValue: dayjs()
          .subtract(7, "days")
          .startOf("day")
          .format("YYYY-MM-DD"),
      },
      to_date: {
        serialize: (v: string) => v || null,
        deserialize: (v: string) => v,
        defaultValue: dayjs().endOf("day").format("YYYY-MM-DD"),
      },
      category: {
        serialize: (v: string) => v || null,
        deserialize: (v: string) => v,
        defaultValue: "",
      },
    },
    enableSync: true,
    replaceHistory: false,
  });

  // Convert URL filter dates to Dayjs objects for date range
  const dateRange: [Dayjs, Dayjs] = useMemo(
    () => [dayjs(filters.from_date), dayjs(filters.to_date)],
    [filters.from_date, filters.to_date]
  );

  const selectedCategory = filters.category;

  const [queryParams, setQueryParams] = useState<{
    site_id: SiteId;
    pump_id: string;
    from_date: string;
    to_date: string;
  }>({
    site_id: siteId,
    pump_id: selectedCategory,
    from_date: filters.from_date,
    to_date: filters.to_date,
  });

  const { data: pumpCategories = [], isLoading: isPumpCategoriesLoading } =
    useGetPumpCategoriesQuery(siteId);

  const {
    data: heatmapData,
    isLoading: isHeatmapLoading,
    isFetching: isHeatmapFetching,
    error: heatmapError,
  } = useGetPumpHeatmapDataQuery(queryParams, {
    skip: !selectedCategory || !queryParams.pump_id,
  });

  // If API returns usedLastSevenDaysDB true, update dateRange from API response

  useEffect(() => {
    if (
      selectedCategory &&
      !isHeatmapLoading &&
      !isHeatmapFetching &&
      heatmapData
    ) {
      setInitialDateSet(true);
      hasLoadedOnce.current = true;
    }
  }, [isHeatmapLoading, isHeatmapFetching, heatmapData, selectedCategory]);

  const handleDateRangeChange = useCallback(
    (dates: DateRangePickerType) => {
      if (dates && dates[0] && dates[1] && !isSettingFromAPI.current) {
        setUrlFilters({
          from_date: dates[0].format("YYYY-MM-DD"),
          to_date: dates[1].format("YYYY-MM-DD"),
        });
      }
      isSettingFromAPI.current = false;
    },
    [setUrlFilters]
  );

  const handleTabChange = useCallback(
    (categoryId: string) => {
      setFilter("category", categoryId);
    },
    [setFilter]
  );

  useEffect(() => {
    if (
      pumpCategories &&
      Array.isArray(pumpCategories) &&
      pumpCategories.length > 0 &&
      !selectedCategory &&
      urlFiltersReady
    ) {
      const firstCategory = pumpCategories[0]?.id;
      if (firstCategory) {
        setFilter("category", firstCategory);
      }
    }
  }, [pumpCategories, selectedCategory, setFilter, urlFiltersReady]);

  useEffect(() => {
    if (urlFiltersReady) {
      setQueryParams({
        site_id: siteId,
        pump_id: selectedCategory,
        from_date: filters.from_date,
        to_date: filters.to_date,
      });
    }
  }, [
    siteId,
    selectedCategory,
    filters.from_date,
    filters.to_date,
    urlFiltersReady,
  ]);

  const chartTitle = useMemo(() => {
    const formattedCategory = selectedCategory?.replace(/_/g, " ");
    return selectedCategory ? `${formattedCategory}` : "Select a pump category";
  }, [selectedCategory]);

  const processedHeatmapData = useMemo<any[]>(
    () =>
      Array.isArray(heatmapData?.data?.columnData)
        ? (heatmapData?.data?.columnData ?? [])
        : [],
    [heatmapData?.data?.columnData]
  );
  const chartHeight = useMemo(() => {
    const data = processedHeatmapData;
    if (!Array.isArray(data) || data.length === 0) return 600;
    if (data.length > 0) {
      const attributes = data
        .slice(1)
        .filter(
          (item: any) =>
            item.columnName !== "Pump ID" &&
            !possibleDateColumnTypes.includes(item.columnType) &&
            item.columnType !== "string"
        );
      const baseHeight = 165;
      const heightPerAttribute = 14;
      const calculatedHeight =
        baseHeight + attributes.length * heightPerAttribute;
      return Math.max(500, Math.min(calculatedHeight, 1500));
    }
    return 600;
  }, [processedHeatmapData]);

  const hasFilters = Boolean(selectedCategory);
  const showOverlaySpinner =
    (isHeatmapLoading || isHeatmapFetching) && hasLoadedOnce.current;
  const isInitialLoading = isPumpCategoriesLoading || !hasFilters;

  return (
    <PumpHeatmapContext.Provider
      value={{
        dateRange,
        selectedCategory,
        pumpCategories,
        heatmapData,
        heatmapError,
        handleDateRangeChange,
        handleTabChange,
        chartTitle,
        processedHeatmapData,
        chartHeight,
        showOverlaySpinner,
        isInitialLoading,
        initialDateSet,
        heatmapLoading: isHeatmapLoading,
        heatmapFetching: isHeatmapFetching,
        siteId,
      }}
    >
      {children}
    </PumpHeatmapContext.Provider>
  );
};

export const usePumpHeatmapContext = () => {
  const context = useContext(PumpHeatmapContext);
  if (!context)
    throw new Error(
      "usePumpHeatmapContext must be used within PumpHeatmapProvider"
    );
  return context;
};
