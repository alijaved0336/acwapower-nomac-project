"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  useRef,
} from "react";

import {
  Analysis,
  AnalysisTableFilter,
} from "../../../../../types/analysis.types";
import {
  useDeleteAnalysisMutation,
  useGetAllAnalysisQuery,
} from "../../../../../store/api/analysisApi";
import { DateFilter, PaginationFilter } from "../../../../../types/api.types";
import { Dayjs } from "dayjs";
import { getFormattedDate } from "../../../../../utils/helpers";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import ConfirmationModal from "../../../../common/modals/ConfirmationModal";
import { ErrorResponse } from "../../../../../store/services/axiosBaseQuery";
import { notification } from "antd";
import { useNotification } from "../../../../../hooks";

type ColumnDef = {
  key: string;
  label: string;
};

const columnDefs = [
  // { key: "id", label: "ID" },
  { key: "name", label: "Template Name" },
  { key: "asset_type", label: "Asset Type" },
  { key: "visibility", label: "Visibility" },
  { key: "updated_at", label: "Updated At" },
  { key: "user_name", label: "Created By" },
  { key: "action", label: "Action" },
] as ColumnDef[];

type ColumnKey = (typeof columnDefs)[number]["key"];

type AnalysisListContextType = {
  analysisList: Array<Analysis>;
  isFetchingAnalysis: boolean;
  total: number;
  filters: PaginationFilter;
  visibleCols: ColumnKey[];
  columnDefs: ColumnDef[];
  search: string;
  visibilityFilter: string;
  dateFilter: DateFilter | null;
  setVisibleCols: React.Dispatch<React.SetStateAction<ColumnKey[]>>;
  handlePaginationChange: (pageNumber: number, pageSize: number) => void;
  handleSearch: (searchTerm: string) => void;
  handleDatesChange: (newDates: [Dayjs | null, Dayjs | null] | null) => void;
  handleVisibilityFilter: (visibility: string) => void;
  handleOpenRemoveAnaysisModal: (analysis: Analysis) => void;
  applyFilters: () => void;
  resetFilters: () => void;
};

const AnalysisListContext = createContext<AnalysisListContextType | null>(null);

// Column registry used for show/hide UI

export const AnalysisListProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  // URL-synced filters for better UX and shareability
  const {
    filters,
    setFilter,
    setFilters: setUrlFilters,
  } = useUrlFilters<AnalysisTableFilter>({
    filterConfig: {
      page: createFilterConfig.number(1),
      limit: createFilterConfig.number(10),
      visibility: createFilterConfig.string("All", true),
      name: createFilterConfig.string(""),
      from_date: {
        serialize: (v: string | null) => v || null,
        deserialize: (v: string) => v,
        defaultValue: null,
      },
      to_date: {
        serialize: (v: string | null) => v || null,
        deserialize: (v: string) => v,
        defaultValue: null,
      },
    },
    enableSync: true,
    replaceHistory: false,
  });

  // Initialize intermediate filters from URL filters on mount
  const [search, setSearch] = useState<string>(filters.name || "");
  const [visibilityFilter, setVisibilityFilter] = useState<string>(
    filters.visibility || "All"
  );
  const [dateFilter, setDateFilter] = useState<DateFilter | null>(
    filters.from_date && filters.to_date
      ? { from_date: filters.from_date, to_date: filters.to_date }
      : null
  );

  const [visibleCols, setVisibleCols] = useState<ColumnKey[]>(
    columnDefs.map((c) => c.key)
  );
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(
    null
  );

  const notification = useNotification();

  // Track if we're syncing from URL to prevent feedback loops
  const isSyncingFromUrl = useRef(false);

  const [deleteAnalysis, { isLoading: isRemovingAnalysis }] =
    useDeleteAnalysisMutation();

  // Sync URL filters to intermediate states on URL change (e.g., browser back/forward, page refresh)
  useEffect(() => {
    isSyncingFromUrl.current = true;

    if (filters.name !== search) {
      setSearch(filters.name || "");
    }
    if (filters.visibility !== visibilityFilter) {
      setVisibilityFilter(filters.visibility || "All");
    }
    if (filters.from_date && filters.to_date) {
      const newDateFilter = {
        from_date: filters.from_date,
        to_date: filters.to_date,
      };
      if (
        !dateFilter ||
        dateFilter.from_date !== newDateFilter.from_date ||
        dateFilter.to_date !== newDateFilter.to_date
      ) {
        setDateFilter(newDateFilter);
      }
    } else if (dateFilter !== null && !filters.from_date && !filters.to_date) {
      setDateFilter(null);
    }

    // Reset flag after sync
    setTimeout(() => {
      isSyncingFromUrl.current = false;
    }, 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.name, filters.visibility, filters.from_date, filters.to_date]);

  // Debounce search to prevent excessive API calls
  // Only update URL if search changed from user input (not from URL sync)
  useEffect(() => {
    if (isSyncingFromUrl.current) {
      return; // Skip URL update if we're syncing from URL
    }

    const timer = setTimeout(() => {
      if (search !== filters.name) {
        setUrlFilters({ name: search, page: 1 });
      }
    }, 500); // 500ms delay

    return () => clearTimeout(timer);
  }, [search, filters.name, setUrlFilters]);

  const {
    data: analysisData,
    isLoading,
    isFetching,
  } = useGetAllAnalysisQuery(
    {
      ...filters,
      name: filters.name || undefined,
      visibility: filters.visibility !== "All" ? filters.visibility : undefined,
    },
    {
      // Remove refetchOnMountOrArgChange to prevent unnecessary refetches
    }
  );

  const analysisList = analysisData?.items || ([] as Array<Analysis>);
  const isFetchingAnalysis = isLoading || isFetching;
  const total = analysisData?.total || 0;

  const handlePaginationChange = useCallback(
    (pageNumber: number, pageSize: number) => {
      setUrlFilters({ page: pageNumber, limit: pageSize });
    },
    [setUrlFilters]
  );

  const handleSearch = useCallback((searchTerm: string) => {
    setSearch(searchTerm);
  }, []);

  const handleDatesChange = useCallback(
    (newDates: [Dayjs | null, Dayjs | null] | null) => {
      if (newDates) {
        const [fromDate, toDate] = newDates;
        const formattedFromDate = getFormattedDate(fromDate, "YYYY-MM-DD");
        const formattedToDate = getFormattedDate(toDate, "YYYY-MM-DD");

        setDateFilter({
          from_date: formattedFromDate,
          to_date: formattedToDate,
        });
      } else {
        setDateFilter(null);
      }
    },
    []
  );

  const handleVisibilityFilter = useCallback((visibility: string) => {
    setVisibilityFilter(visibility);
  }, []);

  const handleOpenRemoveAnaysisModal = useCallback((analysis: Analysis) => {
    setSelectedAnalysis(analysis);
    setOpenConfirmationModal(true);
  }, []);

  const handleRemoveAnalysis = useCallback(async () => {
    try {
      const response = await deleteAnalysis(
        selectedAnalysis?.id ?? ""
      ).unwrap();

      notification.showSuccess(
        response.message ?? "Analysis deleted successfully!"
      );

      setOpenConfirmationModal(false);
      setSelectedAnalysis(null);
    } catch (error: unknown) {
      // Type guard to safely access error properties
      const err = error as ErrorResponse;
      notification.showError(
        typeof err.data === "string" ? err.data : "Unable to delete analysis"
      );
    }
    console.log({ selectedAnalysis });
  }, [selectedAnalysis, deleteAnalysis, notification]);

  const handleCancelRemoveAnalysis = useCallback(() => {
    console.log({ selectedAnalysis });
    setSelectedAnalysis(null);
    setOpenConfirmationModal(false);
  }, [selectedAnalysis]);

  const applyFilters = useCallback(() => {
    setUrlFilters({
      page: 1,
      visibility: visibilityFilter,
      from_date: dateFilter ? dateFilter.from_date : null,
      to_date: dateFilter ? dateFilter.to_date : null,
    }); // Reset to first page when applying filters
  }, [visibilityFilter, dateFilter, setUrlFilters]);

  const resetFilters = useCallback(() => {
    setVisibilityFilter("All");
    setDateFilter(null);
    setSearch("");
    setUrlFilters({
      page: 1,
      visibility: "All",
      name: "",
      from_date: null,
      to_date: null,
    });
  }, [setUrlFilters]);

  const value = useMemo(
    () => ({
      analysisList,
      isFetchingAnalysis,
      total,
      filters,
      visibleCols,
      columnDefs,
      search,
      visibilityFilter,
      dateFilter,
      setVisibleCols,
      handlePaginationChange,
      handleSearch,
      handleVisibilityFilter,
      applyFilters,
      resetFilters,
      handleDatesChange,
      handleOpenRemoveAnaysisModal,
    }),
    [
      analysisList,
      isFetchingAnalysis,
      total,
      filters,
      visibleCols,
      search,
      visibilityFilter,
      dateFilter,
      handlePaginationChange,
      handleSearch,
      handleVisibilityFilter,
      handleDatesChange,
      applyFilters,
      resetFilters,
      setVisibleCols,
      handleOpenRemoveAnaysisModal,
    ]
  );

  return (
    <AnalysisListContext.Provider value={value}>
      <ConfirmationModal
        open={openConfirmationModal}
        title="Are you sure you want to remove this Analysis?"
        itemName={selectedAnalysis?.name}
        confirmText="Yes, Remove"
        cancelText="Cancel"
        onConfirm={handleRemoveAnalysis}
        onCancel={handleCancelRemoveAnalysis}
        confirmButtonType="danger"
        loading={isRemovingAnalysis}
      />
      {children}
    </AnalysisListContext.Provider>
  );
};

export const useAnalysisList = () => {
  const context = useContext(AnalysisListContext);
  if (!context) {
    throw new Error("useAnalysis must be used within AnalysisProvider");
  }
  return context;
};
