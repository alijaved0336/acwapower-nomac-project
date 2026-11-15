import { useState, useEffect } from "react";
import dayjs, { Dayjs } from "dayjs";
import {
  useGetPumpCategoriesQuery,
  useGetCardsDataQuery,
  useGetPumpKPIsQuery,
  useGetActionsOverviewQuery,
} from "@/store/api/PumpsApi";
import { getFormattedDate } from "../../../../../utils/helpers";
import { DateFormat } from "../../../../../constants/enums";
import { DateRangePickerType } from "../../../../../types/common.types";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";

// Type for URL filters
interface PumpPerformanceFilters {
  selectedDate: string; // Store as ISO string for URL compatibility
}

export const usePumpPerformanceState = (siteId: string) => {
  // URL-synced filters for better UX and shareability
  const { filters, setFilter } = useUrlFilters<PumpPerformanceFilters>({
    filterConfig: {
      selectedDate: {
        serialize: (v: string) => v || null,
        deserialize: (v: string) => v,
        defaultValue: dayjs().startOf("day").toISOString(),
      },
    },
    enableSync: true,
    replaceHistory: false,
  });

  // Convert URL string back to Dayjs for internal use
  const selectedDate = dayjs(filters.selectedDate);
  const [dateRange, setDateRange] = useState<DateRangePickerType>(null);

  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [activeTab, setActiveTab] = useState<string>("");
  const [selectedPumps, setSelectedPumps] = useState<string[]>([]);
  const [isTabChanging, setIsTabChanging] = useState(false);
  const [previousCategory, setPreviousCategory] = useState<string>("");

  const {
    data: categoriesData,
    isError,
    error,
  } = useGetPumpCategoriesQuery(siteId);
  const pumpCategories = categoriesData?.categories || [];

  useEffect(() => {
    if (pumpCategories.length > 0 && !activeTab) {
      const firstCategory = pumpCategories[0];
      setActiveTab(firstCategory.id);
      setSelectedCategory(firstCategory.id);
      setPreviousCategory(firstCategory.id);
    }
  }, [pumpCategories, activeTab]);

  // Format date to UTC
  const formatDateToUTC = (date: Dayjs | null) => {
    if (!date) return undefined;
    return date.format("YYYY-MM-DDTHH:mm:ss") + "Z";
  };

  const {
    data: cardsData,
    isLoading: cardsLoading,
    isFetching: cardsFetching,
  } = useGetCardsDataQuery(
    {
      site_id: siteId,
      pump_id: selectedCategory,
      ...(selectedDate && {
        date: getFormattedDate(
          selectedDate,
          DateFormat.DATE_TIME_24H_UTC,
          true
        ),
      }),
    },
    { skip: !selectedCategory }
  );

  const {
    data: kpiData,
    isLoading: kpisLoading,
    isFetching: kpisFetching,
  } = useGetPumpKPIsQuery(
    {
      site_id: siteId,
      pump_id: selectedCategory,
      ...(selectedDate && {
        date: formatDateToUTC(selectedDate),
      }),
    },
    { skip: !selectedCategory }
  );

  const {
    data: actionsData,
    isLoading: actionsLoading,
    isFetching: actionsFetching,
  } = useGetActionsOverviewQuery(
    {
      site_id: siteId,
      pump_id: selectedCategory,
      pumps: selectedPumps.length > 0 ? selectedPumps.join(",") : undefined,
      ...(dateRange && dateRange[0] && dateRange[1]
        ? {
            from_date: formatDateToUTC(dateRange[0]),
            to_date: formatDateToUTC(dateRange[1]),
          }
        : selectedDate && {
            from_date: formatDateToUTC(selectedDate),
          }),
    },
    { skip: !selectedCategory, refetchOnMountOrArgChange: true }
  );

  useEffect(() => {
    if (
      isTabChanging &&
      selectedCategory &&
      selectedCategory !== previousCategory
    ) {
      const allLoaded =
        !cardsLoading &&
        !kpisLoading &&
        !actionsLoading &&
        !cardsFetching &&
        !kpisFetching &&
        !actionsFetching;

      if (allLoaded && cardsData && kpiData && actionsData) {
        setIsTabChanging(false);
        setPreviousCategory(selectedCategory);
      }
    }
  }, [
    isTabChanging,
    selectedCategory,
    previousCategory,
    cardsLoading,
    kpisLoading,
    actionsLoading,
    cardsFetching,
    kpisFetching,
    actionsFetching,
    cardsData,
    kpiData,
    actionsData,
  ]);

  const handleDateChange = (date: Dayjs | null) => {
    if (date) {
      setFilter("selectedDate", date.toISOString());
    }

    setDateRange(null);
  };

  const handleDateRangeChange = (dates: DateRangePickerType) => {
    setDateRange(dates);
  };

  const handleCategoryChange = (category: string) => {
    if (category !== selectedCategory) {
      setIsTabChanging(true);
      setSelectedCategory(category);
      setSelectedPumps([]);
    }
  };

  const handleTabChange = (tab: string) => {
    if (tab !== activeTab) {
      setIsTabChanging(true);
      setActiveTab(tab);
    }
  };

  return {
    siteId,
    selectedDate,
    dateRange,
    selectedCategory,
    activeTab,
    selectedPumps,
    pumpCategories,
    isTabChanging,
    setSelectedDate: handleDateChange,
    setDateRange: handleDateRangeChange,
    setSelectedCategory: handleCategoryChange,
    setActiveTab: handleTabChange,
    setSelectedPumps,
    cardsData,
    kpiData,
    actionsData,
    cardsLoading: cardsLoading || cardsFetching,
    kpisLoading: kpisLoading || kpisFetching,
    actionsLoading: actionsLoading || actionsFetching,
    isError,
    error,
  };
};
