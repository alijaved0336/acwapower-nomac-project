"use client";
import React, {
  useState,
  useCallback,
  useMemo,
  useEffect,
  useTransition,
  useRef,
  Suspense,
} from "react";
import {
  DragEndEvent, // Regular import - just a type
  DragStartEvent, // Regular import - just a type
  PointerSensor, // Regular import - class
  useSensor, // Regular import - hook
  useSensors, // Regular import - hook
} from "@dnd-kit/core";

// ✅ ONLY make the DndContext component dynamic

import {
  Column,
  DateFilter,
  ColumnData,
  SaveWidgetsPayload,
  Table,
  Widget,
  WidgetResponse,
  Site,
} from "../../../../../types/analysis.types";
import { v4 as uuidv4 } from "uuid";
import { WIDGET_OPTIONS } from "../constants/constants";
import { getFilteredWidgets, validateColumnDrop } from "../utils/utils";

import {
  useGetAllWidgetsByAnalysisQuery,
  useLazyGetDataByColumnsQuery,
  useSaveWidgetsMutation,
  useCopyWidgetMutation,
  useGetAllColumnsByTableAndSiteQuery,
  useGetAllSitesQuery,
  useGetAllTablesBySiteQuery,
} from "../../../../../store/api/analysisApi";

import isEmpty from "lodash/isEmpty";
import uniqBy from "lodash/uniqBy";

import { useParams, useRouter, useSearchParams } from "next/navigation";

import {
  generateTimeSlots,
  getFormattedDate,
} from "../../../../../utils/helpers";
import dayjs, { Dayjs } from "dayjs";
import { createContext, useContextSelector } from "use-context-selector";
import { ErrorResponse } from "../../../../../store/services/axiosBaseQuery";

import { useAppSelector, useNotification } from "../../../../../hooks";
import { SerializedError } from "@reduxjs/toolkit";
import { DateFormat } from "../../../../../constants/enums";
import { arrayMove } from "@dnd-kit/sortable";
import { EChartsYAxisConfig } from "../../../../../utils/chartConfig";

import { DateRangePickerType } from "../../../../../types/common.types";
import dynamic from "next/dynamic";
import { ECharts } from "echarts";
import { possibleDateColumnTypes } from "../../../../../constants/states";

const DndContext = dynamic(
  () => import("@dnd-kit/core").then((mod) => mod.DndContext),
  { ssr: false }
);
const DisableEchartsPointerEventsOnDrag = dynamic(
  () => import("../AnalysisTemplate/DisableApexPointerEventsOnDrag"),
  { ssr: false }
);

type AnalysisTemplateContextType = {
  widgets: Widget[];
  activeItem: Column | null;
  activeWidget: Widget | null;

  selectedWidgetId?: string;
  selectedSite: string;
  selectedTables: Array<Table>;
  defaultXCategory: string[];
  analysisName: string;
  visibility: "public" | "private";

  dateFilter: DateFilter | null;

  chartRefs: React.RefObject<
    Record<string, { snapshot: string; instance: ECharts | null }>
  >;

  widgetLoading: WidgetLoadingState;
  isFiltering: boolean;
  isSavingWidgets: boolean;

  isFetchingWidgets: boolean;
  isPendingDrop: boolean;

  widgetsError: ErrorResponse | SerializedError | undefined;

  // API data for sites, tables, and columns
  sites: Site[];
  isFetchingSites: boolean;
  sitesError: ErrorResponse | SerializedError | undefined;

  tables: Table[];
  isFetchingTables: boolean;
  tablesError: ErrorResponse | SerializedError | undefined;

  columns: Column[];
  isFetchingColumns: boolean;
  columnsError: ErrorResponse | SerializedError | undefined;

  // Add modal state
  isAddWidgetModalOpen: boolean;

  isCopyingWidget: boolean;
  selectedRack: string[] | null;
  widgetSelectedRacks: Record<string, string[] | null>;
  allWidgetTables: Array<Table>;

  setActiveItem: React.Dispatch<React.SetStateAction<Column | null>>;
  handleSelectSite: (site: string) => void;
  handleSelectTables: (tables: Array<Table>) => void;
  handleChangeAnalysisName: (name: string) => void;
  handleChangeVisibility: (visibility: "public" | "private") => void;
  handleSelectWidget: (widgetId: string) => void;
  handleClickWidget: (column: Column[]) => void;
  handleAddNewWidget: () => void;
  handleRemoveWidget: (widgetId: string) => void;
  handleDragEnd: (event: DragEndEvent) => void;
  handleDatesChange: (newDates: [Dayjs | null, Dayjs | null] | null) => void;
  handleChangeWidgetName: (widgetId: string, name: string) => void;
  handleSaveWidgets: () => void;
  handleSelectRack: (rack: string[] | null) => void;
  handleSelectWidgetRack: (widgetId: string, rack: string[] | null) => void;
  handleResetFilters: () => void;
  handleCopyWidget: (
    widgetId: string,
    targetAnalysisId: string,
    newWidgetName?: string
  ) => Promise<void>;

  // Add modal handlers
  handleOpenAddWidgetModal: () => void;
  handleCloseAddWidgetModal: () => void;
  handleSetWidgetSnapshot: (
    widgetId: string,
    snapshot: string,
    instance: ECharts | null
  ) => void;
  handleSetYaxisOptions: (
    widgetId: string,
    yAxisOptions: Array<EChartsYAxisConfig>
  ) => void;
  handleRemoveColumnFromWidget: (
    widgetId: string,
    columnName: string,
    tableName: string,
    siteName: string
  ) => void;
};

type WidgetLoadingState = {
  [widgetId: string]: boolean;
};

export const AnalysisTemplateContext =
  createContext<AnalysisTemplateContextType>({} as AnalysisTemplateContextType);

export const AnalysisTemplateProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const params = useParams(); // { id: "5ba72a25-a764-469e-95e7-86752bddd68c" }
  const searchParams = useSearchParams();
  const analysisId = params.slug as string;
  const router = useRouter();
  const notification = useNotification();
  const [isPending, startTransition] = useTransition();

  const user = useAppSelector((state) => state.auth.user);

  const chartRefs = useRef<
    Record<string, { snapshot: string; instance: ECharts | null }>
  >({});

  const lastOverIds = useRef<{ activeId: string; overId: string } | null>(null);
  const processedWidgetsRef = useRef<Set<string>>(new Set());
  const widgetsRef = useRef<Widget[]>([]);
  const hasRefetchedRacksOnLoad = useRef<string | null>(null);

  // Store chart instance in the map

  // Get analysis name and visibility from query parameters
  const analysisNameFromQuery = searchParams.get("name");
  const visibilityFromQuery = searchParams.get("visibility");

  const [widgets, setWidgets] = useState<Widget[]>([]);

  // Keep ref in sync with widgets
  useEffect(() => {
    widgetsRef.current = widgets;
  }, [widgets]);
  const [selectedWidgetId, setSelectedWidgetId] = useState<string>();

  const [activeItem, setActiveItem] = useState<Column | null>(null);
  const [activeWidget, setActiveWidget] = useState<Widget | null>(null);

  const [selectedSite, setSelectedSite] = useState<string>("");
  const [selectedTables, setSelectedTables] = useState<Array<Table>>([]);

  const [widgetLoading, setWidgetLoading] = useState<WidgetLoadingState>({});
  const [isFiltering, setIsFiltering] = useState<boolean>(false);

  // Initialize analysis name from query parameter or default
  const [analysisName, setAnalysisName] = useState(
    analysisNameFromQuery || "Default analysis"
  );

  const [assetType, setAssetType] = useState("");
  const [analysisType, setAnalysisType] = useState("");

  const [dateFilter, setDateFilter] = useState<DateFilter | null>({
    from_date: getFormattedDate(
      dayjs().add(-7, "d").startOf("d"),
      DateFormat.DATE_TIME_24H
    ),
    to_date: getFormattedDate(dayjs().endOf("d"), DateFormat.DATE_TIME_24H),
  });

  // Initialize visibility from query parameter or default to "public"
  const [visibility, setVisibility] = useState<"public" | "private">(
    (visibilityFromQuery as "public" | "private") || "public"
  );

  // Add selectedRack state (global - for sidebar)
  const [selectedRack, setSelectedRack] = useState<string[] | null>(null);

  // Add widget-specific rack selection state
  const [widgetSelectedRacks, setWidgetSelectedRacks] = useState<
    Record<string, string[] | null>
  >({});

  // Add modal state
  const [isAddWidgetModalOpen, setIsAddWidgetModalOpen] = useState(false);
  // At the top with other hooks
  const [getDataByColumns] = useLazyGetDataByColumnsQuery();

  // Sites API
  const {
    sites: sitesData,
    isFetchingSites,
    sitesError,
  } = useGetAllSitesQuery(undefined, {
    selectFromResult: ({ data, isLoading, isFetching, error }) => ({
      sites: data || [],
      isFetchingSites: isLoading || isFetching,
      sitesError: error,
    }),
  });

  // Tables API
  const {
    tables: tablesData,
    isFetchingTables,
    tablesError,
  } = useGetAllTablesBySiteQuery(selectedSite, {
    selectFromResult: ({ data, isLoading, isFetching, error }) => ({
      tables: data || [],
      isFetchingTables: isLoading || isFetching,
      tablesError: error,
    }),
    skip: !selectedSite,
  });

  // Columns API
  const {
    columns: columnsData,
    isFetchingColumns,
    columnsError,
  } = useGetAllColumnsByTableAndSiteQuery(selectedTables, {
    selectFromResult: ({ data, isLoading, isFetching, error }) => ({
      columns: selectedTables.length === 0 ? [] : data || [],
      isFetchingColumns: isLoading || isFetching,
      columnsError: error,
    }),
    skip: selectedTables.length === 0,
  });

  useEffect(() => {
    const autoPlotDateTime = async () => {
      // Use ref to get current widgets without causing dependency issues
      const currentWidgets = widgetsRef.current;

      // Only proceed if we have site, tables, dateFilter, and at least one widget
      if (
        !selectedSite ||
        selectedTables.length === 0 ||
        currentWidgets.length === 0 ||
        !dateFilter
      ) {
        return;
      }

      // ✅ Find all empty widgets for chart types that need x-axis
      const chartTypesWithXAxis = ["line"];
      const emptyWidgets = currentWidgets.filter(
        (w) => w.columns.length === 0 && chartTypesWithXAxis.includes(w.type)
      );
      if (emptyWidgets.length === 0) {
        // Reset processed ref when all widgets have columns
        processedWidgetsRef.current.clear();
        return;
      }

      // Process each empty widget
      for (const emptyWidget of emptyWidgets) {
        // Check if we've already processed this widget with these exact conditions
        const widgetKey = `${emptyWidget.id}-${selectedSite}-${selectedTables.map((t) => `${t.siteName}:${t.tableName}`).join(",")}-${dateFilter.from_date}-${dateFilter.to_date}`;
        if (processedWidgetsRef.current.has(widgetKey)) {
          continue;
        }

        try {
          // ✅ Show loading spinner for the empty widget
          setWidgetLoading((prev) => ({ ...prev, [emptyWidget.id]: true }));

          // ✅ Use available columns from context
          const availableColumns = columnsData;

          if (!availableColumns || availableColumns.length === 0) {
            setWidgetLoading((prev) => ({ ...prev, [emptyWidget.id]: false }));
            continue;
          }

          // Find DateTime or Timestamp column
          const dateTimeColumn = availableColumns.find((col: Column) =>
            possibleDateColumnTypes.includes(col.columnType)
          );

          if (!dateTimeColumn) {
            setWidgetLoading((prev) => ({ ...prev, [emptyWidget.id]: false }));
            continue;
          }

          // Fetch data for this column
          const data = await getDataByColumns({
            columns: [
              {
                columnName: dateTimeColumn.columnName,
                columnType: dateTimeColumn.columnType,
                siteName: dateTimeColumn.siteName,
                tableName: dateTimeColumn.tableName,
              },
            ],
            from_date: dateFilter.from_date,
            to_date: dateFilter.to_date,
            rack: selectedRack,
          }).unwrap();

          const columnData = data[0];

          if (columnData?.dataSource && columnData.dataSource.length) {
            const newColumn: ColumnData = {
              siteName: dateTimeColumn.siteName,
              tableName: dateTimeColumn.tableName,
              columnName: dateTimeColumn.columnName,
              columnType: dateTimeColumn.columnType,
              dataSource: columnData.dataSource,
              racks: columnData.racks,
            };

            // ✅ Add this column to the empty widget
            setWidgets((prev) =>
              prev.map((widget) =>
                widget.id === emptyWidget.id && widget.columns.length === 0
                  ? { ...widget, columns: [newColumn] }
                  : widget
              )
            );

            // Mark as processed
            processedWidgetsRef.current.add(widgetKey);
          }
        } catch (error) {
          console.error("Error auto-plotting DateTime column:", error);
        } finally {
          // ✅ Hide loading spinner
          setWidgetLoading((prev) => ({ ...prev, [emptyWidget.id]: false }));
        }
      }
    };

    autoPlotDateTime();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selectedSite,
    selectedTables,
    dateFilter?.from_date,
    dateFilter?.to_date,
    columnsData?.length,
    selectedRack,
    widgets.length, // Add widgets.length to detect new widgets
  ]);

  // Add selectedRack handler
  const handleSelectRack = useCallback(
    async (rack: string[] | null) => {
      setSelectedRack(rack);

      const allColumns = widgets
        .flatMap((w) => w.columns)
        .filter((col, index, self) => self.indexOf(col) === index);

      const uniqueColumns = uniqBy(
        allColumns,
        (c) => `${c.siteName}::${c.tableName}::${c.columnName}::${c.columnType}`
      );

      if (!uniqueColumns.length) return;

      try {
        setIsFiltering(true);
        const data = await getDataByColumns({
          columns: uniqueColumns,
          from_date: dateFilter?.from_date ?? "",
          to_date: dateFilter?.to_date ?? "",
          rack: rack,
        }).unwrap();

        startTransition(() => {
          const filteredWidgets = getFilteredWidgets(widgets, data);
          setWidgets(filteredWidgets);
        });
      } catch (error) {
      } finally {
        setIsFiltering(false);
      }
    },
    [widgets, dateFilter, getDataByColumns]
  );

  // Widget-specific rack selection handler
  const handleSelectWidgetRack = useCallback(
    async (widgetId: string, rack: string[] | null) => {
      setWidgetSelectedRacks((prev) => ({
        ...prev,
        [widgetId]: rack,
      }));

      // Find the specific widget
      const targetWidget = widgets.find((w) => w.id === widgetId);
      if (
        !targetWidget ||
        !targetWidget.columns ||
        !targetWidget.columns.length
      )
        return;

      const validColumns = targetWidget.columns.filter(
        (c) => c && c.siteName && c.tableName && c.columnName && c.columnType
      );

      if (!validColumns.length) return;

      const uniqueColumns = uniqBy(
        validColumns,
        (c) => `${c.siteName}::${c.tableName}::${c.columnName}::${c.columnType}`
      ).map((col) => ({
        columnName: col.columnName,
        columnType: col.columnType,
        siteName: col.siteName,
        tableName: col.tableName,
      }));

      if (!uniqueColumns.length) return;

      try {
        setWidgetLoading((prev) => ({ ...prev, [widgetId]: true }));

        const data = await getDataByColumns({
          columns: uniqueColumns,
          from_date: dateFilter?.from_date ?? "",
          to_date: dateFilter?.to_date ?? "",
          rack: rack,
        }).unwrap();

        const columnDataMap = new Map(
          data.map((colData) => [
            `${colData.siteName}::${colData.tableName}::${colData.columnName}`,
            colData,
          ])
        );

        startTransition(() => {
          setWidgets((prev) =>
            prev.map((w) =>
              w.id === widgetId
                ? {
                    ...w,
                    columns: (w.columns || []).map((col) => {
                      if (
                        !col ||
                        !col.siteName ||
                        !col.tableName ||
                        !col.columnName
                      ) {
                        return col;
                      }
                      const key = `${col.siteName}::${col.tableName}::${col.columnName}`;
                      const updatedData = columnDataMap.get(key);
                      if (updatedData) {
                        return {
                          ...col,
                          dataSource: updatedData.dataSource,
                          racks: updatedData.racks,
                        };
                      }
                      return col;
                    }),
                  }
                : w
            )
          );
        });
      } catch (error) {
        const err = error as ErrorResponse;
        notification.showError(err.data as string, { duration: 3000 });
      } finally {
        setWidgetLoading((prev) => ({ ...prev, [widgetId]: false }));
      }
    },
    [widgets, dateFilter, getDataByColumns, notification]
  );

  const handleResetFilters = useCallback(async () => {
    setSelectedRack(null);
    setWidgetSelectedRacks({}); // Clear all widget-specific racks

    const defaultDateFilter = {
      from_date: getFormattedDate(
        dayjs().add(-7, "d").startOf("d"),
        DateFormat.DATE_TIME_24H
      ),
      to_date: getFormattedDate(dayjs().endOf("d"), DateFormat.DATE_TIME_24H),
    };
    setDateFilter(defaultDateFilter);

    const allColumns = widgets
      .flatMap((w) => w.columns)
      .filter((col, index, self) => self.indexOf(col) === index);

    const uniqueColumns = uniqBy(
      allColumns,
      (c) => `${c.siteName}::${c.tableName}::${c.columnName}::${c.columnType}`
    );

    if (!uniqueColumns.length) return;

    try {
      setIsFiltering(true);

      const data = await getDataByColumns({
        columns: uniqueColumns,
        from_date: defaultDateFilter.from_date,
        to_date: defaultDateFilter.to_date,
        rack: null,
      }).unwrap();

      startTransition(() => {
        const filteredWidgets = getFilteredWidgets(widgets, data);
        setWidgets(filteredWidgets);
      });
    } catch (error) {
    } finally {
      setIsFiltering(false);
    }
  }, [widgets, getDataByColumns]);

  const { widgetsData, isFetchingWidgets, allWidgetsReqStatus, widgetsError } =
    useGetAllWidgetsByAnalysisQuery(analysisId, {
      selectFromResult: ({ data, isLoading, isFetching, status, error }) => ({
        widgetsData: data || ({} as WidgetResponse),
        isFetchingWidgets: isLoading || isFetching,
        allWidgetsReqStatus: status,
        widgetsError: error,
      }),

      // Remove refetchOnMountOrArgChange to prevent unnecessary refetches
    });

  const [saveWidgets, { isLoading: isSavingWidgets }] =
    useSaveWidgetsMutation();

  const [copyWidget, { isLoading: isCopyingWidget }] = useCopyWidgetMutation();

  // Optimized useEffect to handle both site and table selection in one place
  useEffect(() => {
    if (widgetsError) {
      const error = widgetsError as ErrorResponse;

      if (error.status === 404) {
        notification.showError(error.data as string);
        return router.replace("/dashboard/analysis");
      }
    }
  }, [widgetsError, notification, router]);

  useEffect(() => {
    if (allWidgetsReqStatus === "fulfilled" && !isEmpty(widgetsData)) {
      setWidgets(widgetsData.data);
      setAnalysisName(widgetsData.analysis_name);
      setVisibility(widgetsData.visibility);
      const allColumns = widgetsData.data.flatMap((widget) => widget.columns);

      if (allColumns.length > 0) {
        const uniqueSites = [...new Set(allColumns.map((col) => col.siteName))];
        if (uniqueSites.length > 0) {
          setSelectedSite(uniqueSites[0]);
        }

        const uniqueTables = uniqBy(
          allColumns.map((col) => ({
            siteName: col.siteName,
            tableName: col.tableName,
          })),
          (table) => `${table.siteName}::${table.tableName}`
        );

        if (uniqueTables.length > 0) {
          setSelectedTables(uniqueTables);
        }
      }
      setAssetType(widgetsData.asset_type);
      setAnalysisType(widgetsData.analysis_type);

      const restoredWidgetRacks: Record<string, string[] | null> = {};

      widgetsData.data.forEach((widget) => {
        if (
          widget.selectedRacks !== undefined &&
          widget.selectedRacks !== null
        ) {
          if (Array.isArray(widget.selectedRacks)) {
            if (widget.selectedRacks.length > 0) {
              restoredWidgetRacks[widget.id] = widget.selectedRacks;
            }
          } else {
            restoredWidgetRacks[widget.id] = [widget.selectedRacks];
          }
        }
      });

      if (Object.keys(restoredWidgetRacks).length > 0) {
        setWidgetSelectedRacks((prev) => ({
          ...prev,
          ...restoredWidgetRacks,
        }));
        hasRefetchedRacksOnLoad.current = null;
      }

      if (
        !isEmpty(widgetsData.applied_date_filter) &&
        typeof widgetsData.applied_date_filter === "object"
      ) {
        const formattedFromDate = getFormattedDate(
          widgetsData.applied_date_filter.from_date,
          DateFormat.DATE_TIME_24H
        );
        const formattedToDate = getFormattedDate(
          widgetsData.applied_date_filter.to_date,
          DateFormat.DATE_TIME_24H
        );

        setDateFilter({
          from_date: formattedFromDate,
          to_date: formattedToDate,
          rack: widgetsData.applied_date_filter.rack,
        });

        // Also set the selected rack if it exists in the response
        if (widgetsData.applied_date_filter.rack) {
          const rackValue = widgetsData.applied_date_filter.rack;
          setSelectedRack(Array.isArray(rackValue) ? rackValue : [rackValue]);
        }
      }
    }
  }, [allWidgetsReqStatus, widgetsData, analysisId]);

  useEffect(() => {
    if (
      widgets.length === 0 ||
      Object.keys(widgetSelectedRacks).length === 0 ||
      hasRefetchedRacksOnLoad.current === analysisId
    ) {
      return;
    }

    const widgetsToRefetch = widgets.filter(
      (widget) =>
        widgetSelectedRacks[widget.id] &&
        widgetSelectedRacks[widget.id]!.length > 0 &&
        widget.columns &&
        widget.columns.length > 0
    );

    if (widgetsToRefetch.length === 0) {
      hasRefetchedRacksOnLoad.current = analysisId;
      return;
    }

    hasRefetchedRacksOnLoad.current = analysisId;
    (async () => {
      try {
        await Promise.all(
          widgetsToRefetch.map(async (widget) => {
            const widgetRack = widgetSelectedRacks[widget.id];
            if (!widgetRack || widgetRack.length === 0) return;

            const validColumns = (widget.columns || []).filter(
              (c) =>
                c && c.siteName && c.tableName && c.columnName && c.columnType
            );

            if (!validColumns.length) return;

            const uniqueColumns = uniqBy(
              validColumns,
              (c) =>
                `${c.siteName}::${c.tableName}::${c.columnName}::${c.columnType}`
            ).map((col) => ({
              columnName: col.columnName,
              columnType: col.columnType,
              siteName: col.siteName,
              tableName: col.tableName,
            }));

            if (!uniqueColumns.length) return;

            try {
              setWidgetLoading((prev) => ({
                ...prev,
                [widget.id]: true,
              }));

              const data = await getDataByColumns({
                columns: uniqueColumns,
                from_date: dateFilter?.from_date ?? "",
                to_date: dateFilter?.to_date ?? "",
                rack: widgetRack,
              }).unwrap();

              const columnDataMap = new Map(
                data.map((colData) => [
                  `${colData.siteName}::${colData.tableName}::${colData.columnName}`,
                  colData,
                ])
              );

              startTransition(() => {
                setWidgets((prev) =>
                  prev.map((w) =>
                    w.id === widget.id
                      ? {
                          ...w,
                          columns: (w.columns || []).map((col) => {
                            if (
                              !col ||
                              !col.siteName ||
                              !col.tableName ||
                              !col.columnName
                            ) {
                              return col;
                            }
                            const key = `${col.siteName}::${col.tableName}::${col.columnName}`;
                            const updatedData = columnDataMap.get(key);
                            if (updatedData) {
                              return {
                                ...col,
                                dataSource: updatedData.dataSource,
                                racks: updatedData.racks,
                              };
                            }
                            return col;
                          }),
                        }
                      : w
                  )
                );
              });
            } catch (error) {
              console.error(
                `Error refetching data for widget ${widget.id}:`,
                error
              );
            } finally {
              setWidgetLoading((prev) => ({
                ...prev,
                [widget.id]: false,
              }));
            }
          })
        );
      } catch (error) {
        console.error(
          "Error refetching widget data with restored racks:",
          error
        );
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    widgetSelectedRacks,
    analysisId,
    dateFilter,
    getDataByColumns,
    widgets.length,
  ]);

  const handleChangeWidgetName = useCallback(
    (widgetId: string, name: string) => {
      setWidgets((prev) =>
        prev.map((widget) =>
          widget.id === widgetId
            ? {
                ...widget,
                name,
              }
            : widget
        )
      );
    },
    []
  );

  const handleSelectWidget = useCallback((widgetId: string) => {
    setSelectedWidgetId(widgetId);
  }, []);

  const handleSelectSite = useCallback((site: string) => {
    setSelectedSite(site);
    setSelectedTables([]);
  }, []);

  const handleSelectTables = useCallback((checkedTables: Array<Table>) => {
    setSelectedTables(checkedTables);
  }, []);

  const handleChangeAnalysisName = useCallback((name: string) => {
    setAnalysisName(name);
  }, []);

  const handleChangeVisibility = useCallback(
    (visibility: "public" | "private") => {
      setVisibility(visibility);
    },
    []
  );

  const handleRemoveWidget = useCallback(
    (widgetId: string) => {
      const filteredWidgets = widgets?.filter(
        (widget) => widget.id !== widgetId
      );
      setWidgets(filteredWidgets);
    },
    [widgets]
  );

  const handleClickWidget = useCallback(async (columns: Column[]) => {
    const selectedWidgetSite = columns[0].siteName;
    const selectedWidgetTables = columns.map((col) => ({
      siteName: col.siteName,
      tableName: col.tableName,
    }));

    const uniqueTables = uniqBy(
      selectedWidgetTables,
      (t) => `${t.siteName}::${t.tableName}`
    );

    if (selectedWidgetSite) setSelectedSite(selectedWidgetSite);
    if (uniqueTables.length > 0) setSelectedTables(uniqueTables);
  }, []);

  const handleSaveWidgets = useCallback(async () => {
    const mappedWidgets = widgets.map((widget, index) => {
      // Get widget-specific rack selection
      const widgetRack = widgetSelectedRacks[widget.id];

      // Ensure we save selectedRacks properly (array or null, not undefined)
      const selectedRacksToSave =
        widgetRack && widgetRack.length > 0 ? widgetRack : null;

      if (widget.isNew) {
        return {
          type: widget.type,
          columns: widget.columns?.map((col) => ({
            columnName: col.columnName,
            columnType: col.columnType,
            siteName: col.siteName,
            tableName: col.tableName,
          })),
          name: widget.name,
          display_order: index,
          yAxisOptions: widget?.yAxisOptions ?? [],
          selectedRacks: selectedRacksToSave,
        };
      }

      return {
        id: widget.id,
        type: widget.type,
        columns: widget.columns?.map((col) => ({
          columnName: col.columnName,
          columnType: col.columnType,
          siteName: col.siteName,
          tableName: col.tableName,
        })),
        name: widget.name,
        display_order: index,
        yAxisOptions: widget?.yAxisOptions ?? [],
        selectedRacks: selectedRacksToSave,
      };
    }) as Array<Widget>;

    try {
      const widgetsPayload: SaveWidgetsPayload = {
        analysis_id: analysisId,
        analysis_name: analysisName,
        analysis_type: analysisType,
        asset_type: assetType,
        visibility,
        applied_date_filter: dateFilter
          ? {
              ...dateFilter,
              rack: selectedRack || undefined,
            }
          : null,
        user_id: user?.id ?? "unknown",
        widgets: mappedWidgets,
      };

      await saveWidgets(widgetsPayload).unwrap();

      // Update local widgets state to include selectedRacks so they persist
      startTransition(() => {
        setWidgets((prev) =>
          prev.map((widget) => ({
            ...widget,
            selectedRacks: widgetSelectedRacks[widget.id] || null,
            isNew: false,
          }))
        );
      });

      notification.showSuccess("Widgets saved successfully.");
    } catch (error) {
      console.error("Error saving analysis:", error);
      notification.showError("Unable to save widgets.");
    }
  }, [
    saveWidgets,
    widgets,
    widgetSelectedRacks,
    analysisId,
    notification,
    analysisName,
    dateFilter,
    startTransition,
    selectedRack,
    visibility,
    analysisType,
    assetType,
    user,
  ]);

  const handleDatesChange = useCallback(
    async (newDates: DateRangePickerType) => {
      if (newDates) {
        const [fromDate, toDate] = newDates;
        const formattedFromDate = getFormattedDate(
          fromDate,
          DateFormat.DATE_TIME_24H
        );
        const formattedToDate = getFormattedDate(
          toDate,
          DateFormat.DATE_TIME_24H
        );

        setDateFilter({
          from_date: formattedFromDate,
          to_date: formattedToDate,
          rack: selectedRack || undefined,
        });

        // Remove duplicate columns to get optimal response for filteration
        const allColumns = widgets
          .flatMap((w) => w.columns)
          .filter((col, index, self) => self.indexOf(col) === index);

        const uniqueColumns = uniqBy(
          allColumns,
          (c) =>
            `${c.siteName}::${c.tableName}::${c.columnName}::${c.columnType}`
        ).map((col) => ({
          columnName: col.columnName,
          columnType: col.columnType,
          siteName: col.siteName,
          tableName: col.tableName,
        }));

        if (!uniqueColumns.length) return;

        try {
          setIsFiltering(true);

          // Group columns by widget
          const columnsByWidget = new Map<string, Column[]>();
          widgets.forEach((w) => {
            if (!w.columns || !w.columns.length) return;

            const widgetColumns = w.columns
              .filter(
                (col) =>
                  col &&
                  col.siteName &&
                  col.tableName &&
                  col.columnName &&
                  col.columnType
              )
              .map(
                (col) =>
                  ({
                    columnName: col.columnName,
                    columnType: col.columnType,
                    siteName: col.siteName,
                    tableName: col.tableName,
                  }) as Column
              );

            if (widgetColumns.length > 0) {
              columnsByWidget.set(w.id, widgetColumns);
            }
          });

          // Fetch data for each widget with its specific rack filter
          const widgetDataMap = new Map<string, any[]>();
          await Promise.all(
            Array.from(columnsByWidget.entries()).map(
              async ([widgetId, cols]) => {
                const widgetRack =
                  widgetSelectedRacks[widgetId] ?? selectedRack;
                try {
                  const data = await getDataByColumns({
                    columns: cols,
                    from_date: formattedFromDate,
                    to_date: formattedToDate,
                    rack: widgetRack,
                  }).unwrap();
                  widgetDataMap.set(widgetId, data);
                } catch (error) {
                  console.error(
                    `Error fetching data for widget ${widgetId}:`,
                    error
                  );
                }
              }
            )
          );

          // Update widgets with their respective filtered data
          startTransition(() => {
            setWidgets((prev) =>
              prev.map((widget) => {
                const widgetData = widgetDataMap.get(widget.id);
                if (!widgetData) return widget;

                const columnDataMap = new Map(
                  widgetData.map((colData) => [
                    `${colData.siteName}::${colData.tableName}::${colData.columnName}`,
                    colData,
                  ])
                );

                return {
                  ...widget,
                  columns: (widget.columns || []).map((col) => {
                    if (
                      !col ||
                      !col.siteName ||
                      !col.tableName ||
                      !col.columnName
                    ) {
                      return col;
                    }
                    const key = `${col.siteName}::${col.tableName}::${col.columnName}`;
                    const updatedData = columnDataMap.get(key);
                    if (updatedData) {
                      return {
                        ...col,
                        dataSource: updatedData.dataSource,
                        racks: updatedData.racks,
                      };
                    }
                    return col;
                  }),
                };
              })
            );
          });
        } catch (error) {
        } finally {
          setIsFiltering(false);
        }
      } else {
        setDateFilter(null);
      }
    },
    [widgets, getDataByColumns, selectedRack, widgetSelectedRacks]
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event;

    if (active?.data?.current?.type === "sorting") {
      const widget = active?.data?.current?.widget as Widget;

      const snapshot =
        widget.type !== "table" ? chartRefs.current[widget.id]?.snapshot : null;

      setActiveWidget({ ...widget, snapshot });
    } else {
      setActiveItem(event.active.data.current?.data as Column);
    }
  }, []);

  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      setActiveItem(null);
      setActiveWidget(null);

      const { active, over } = event;
      const dragType = active.data?.current?.type;

      // if (!dragType && lastOverIds.current) {
      //   const oldIndex = widgets.findIndex(
      //     (w) => w.id === lastOverIds.current?.activeId
      //   );

      //   const newIndex = widgets.findIndex(
      //     (w) => w.id === lastOverIds.current?.overId
      //   );

      //   const reordered = arrayMove(widgets, oldIndex, newIndex);

      //   lastOverIds.current = null;
      //   setWidgets(reordered);
      // }

      if (dragType === "sorting") {
        if (active.id !== over?.id) {
          const oldIndex = widgets.findIndex((w) => w.id === active.id);
          const newIndex = widgets.findIndex((w) => w.id === over?.id);
          const reordered = arrayMove(widgets, oldIndex, newIndex);

          setWidgets(reordered);
        }
      }

      if (dragType === "plotting") {
        const draggableColumn = active.data?.current?.data as Column;
        const droppableWidgetId = over?.id;

        const targetWidget = widgets?.find(
          (widget) => widget.id === droppableWidgetId
        ) as Widget;

        if (isEmpty(draggableColumn) || isEmpty(targetWidget)) return;

        const errorMessage = validateColumnDrop(draggableColumn, targetWidget);

        if (errorMessage) {
          notification.showError(errorMessage);
          return;
        }

        try {
          setWidgetLoading((prev) => ({ ...prev, [targetWidget.id]: true }));

          // Use widget-specific rack if available, otherwise use global selectedRack
          const widgetRack =
            widgetSelectedRacks[targetWidget.id] ?? selectedRack;

          const data = await getDataByColumns({
            columns: [draggableColumn],
            from_date: dateFilter?.from_date ?? "",
            to_date: dateFilter?.to_date ?? "",
            rack: widgetRack,
          }).unwrap();

          const columnData = data[0];
          const dataSource = columnData.dataSource;
          const racks = columnData?.racks;

          if (!dataSource.length) {
            notification.showError(
              "No data was found against selected date range!"
            );

            setWidgetLoading((prev) => ({ ...prev, [targetWidget.id]: false }));

            return;
          }

          const newColumn = { ...draggableColumn, dataSource, racks };

          const updatedColumns = [...targetWidget.columns, newColumn];

          setWidgets((prev) =>
            prev.map((w) =>
              w.id === droppableWidgetId
                ? {
                    ...w,
                    columns: updatedColumns,
                  }
                : w
            )
          );
        } catch (error) {
          const err = error as ErrorResponse;
          notification.showError(err.data as string, { duration: 3000 });
        } finally {
          setWidgetLoading((prev) => ({ ...prev, [targetWidget.id]: false }));
        }
      }
    },
    [
      widgets,
      getDataByColumns,
      dateFilter,
      notification,
      selectedRack,
      widgetSelectedRacks,
    ]
  );

  const handleCopyWidget = useCallback(
    async (
      widgetId: string,
      targetAnalysisId: string,
      newWidgetName?: string
    ) => {
      try {
        const payload = {
          target_analysis_id: targetAnalysisId,
          ...(newWidgetName && { new_widget_name: newWidgetName }),
        };

        await copyWidget({
          widgetId,
          payload,
        }).unwrap();

        notification.showSuccess("Widget copied successfully.");
      } catch (error) {
        console.error("Failed to copy widget:", error);
        notification.showError("Unable to copy widget.");
      }
    },
    [copyWidget, notification]
  );

  // Add modal handlers
  const handleOpenAddWidgetModal = useCallback(() => {
    setIsAddWidgetModalOpen(true);
  }, []);

  const handleCloseAddWidgetModal = useCallback(() => {
    setIsAddWidgetModalOpen(false);
  }, []);

  const handleAddNewWidget = useCallback(() => {
    const foundWidgetOption = WIDGET_OPTIONS.find(
      (option) => option.id === selectedWidgetId
    );

    if (!foundWidgetOption) return;

    const widgetName =
      foundWidgetOption?.type == "table"
        ? `Table ${widgets.length + 1}`
        : `Chart ${widgets.length + 1}`;

    const newWidget: Widget = {
      id: uuidv4(),
      name: widgetName,
      type: foundWidgetOption.type,
      columns: [],
      yAxisOptions: [],
      isNew: true,
    };

    setWidgets((prev) => [newWidget, ...prev]);
    handleCloseAddWidgetModal();
  }, [selectedWidgetId, handleCloseAddWidgetModal, widgets.length]);

  const handleSetWidgetSnapshot = useCallback(
    (widgetId: string, snapshot: string, instance: ECharts | null) => {
      chartRefs.current[widgetId] = { snapshot, instance };
    },
    []
  );

  const handleSetYaxisOptions = useCallback(
    (widgetId: string, yAxisOptions: Array<EChartsYAxisConfig>) => {
      setWidgets((prev) =>
        prev.map((widget) =>
          widget.id === widgetId ? { ...widget, yAxisOptions } : widget
        )
      );
    },
    []
  );

  const [defaultXCategory, setDefaultXCategory] = useState<string[]>([]);

  useEffect(() => {
    if (dateFilter?.from_date && dateFilter?.to_date) {
      const slots = generateTimeSlots(dateFilter.from_date, dateFilter.to_date)
        .flatMap((dt) => dt.slots)
        .map((sl) => sl.start);
      setDefaultXCategory(slots);
    }
  }, [dateFilter]);

  const handleRemoveColumnFromWidget = useCallback(
    (
      widgetId: string,
      columnName: string,
      tableName: string,
      siteName: string
    ) => {
      setWidgets((prev) =>
        prev.map((widget) =>
          widget.id === widgetId
            ? {
                ...widget,
                columns: widget.columns.filter(
                  (col) =>
                    !(
                      col.columnName === columnName &&
                      col.tableName === tableName &&
                      col.siteName === siteName
                    )
                ),
              }
            : widget
        )
      );
    },
    []
  );

  // Compute all tables used by widgets (for persisting rack options)
  const allWidgetTables = useMemo(() => {
    const widgetTables = new Map<string, Table>();

    // Add selected tables
    selectedTables.forEach((table) => {
      const key = `${table.siteName}::${table.tableName}`;
      widgetTables.set(key, table);
    });

    // Add tables from all widget columns
    widgets.forEach((widget) => {
      if (widget.columns && widget.columns.length > 0) {
        widget.columns.forEach((col) => {
          if (col && col.siteName && col.tableName) {
            const key = `${col.siteName}::${col.tableName}`;
            if (!widgetTables.has(key)) {
              widgetTables.set(key, {
                siteName: col.siteName,
                tableName: col.tableName,
              });
            }
          }
        });
      }
    });

    return Array.from(widgetTables.values());
  }, [widgets, selectedTables]);

  const value = useMemo(
    () => ({
      widgets,
      activeItem,
      activeWidget,
      selectedWidgetId,
      selectedSite,
      selectedTables,
      chartRefs,
      isSavingWidgets,
      isFetchingWidgets,
      isFiltering,
      isPendingDrop: isPending,
      widgetLoading,
      analysisName,
      visibility,
      dateFilter,
      widgetsError,
      isAddWidgetModalOpen,
      selectedRack,
      widgetSelectedRacks,
      allWidgetTables,
      isCopyingWidget,
      defaultXCategory,
      sites: sitesData || [],
      isFetchingSites,
      sitesError,
      tables: tablesData || [],
      isFetchingTables,
      tablesError,
      columns: columnsData || [],
      isFetchingColumns,
      columnsError,
      handleOpenAddWidgetModal,
      handleCloseAddWidgetModal,
      setActiveItem,
      handleChangeAnalysisName,
      handleDatesChange,
      handleChangeVisibility,
      handleSelectSite,
      handleSelectTables,
      handleSelectWidget,
      handleClickWidget,
      handleAddNewWidget,
      handleRemoveWidget,
      handleDragEnd,
      handleChangeWidgetName,
      handleSaveWidgets,
      handleSelectRack,
      handleSelectWidgetRack,
      handleResetFilters,
      handleCopyWidget,
      handleSetWidgetSnapshot,
      handleSetYaxisOptions,
      handleRemoveColumnFromWidget,
    }),
    [
      widgets,
      selectedWidgetId,
      selectedSite,
      selectedTables,
      activeItem,
      activeWidget,
      chartRefs,
      isSavingWidgets,
      isFetchingWidgets,
      isFiltering,
      isPending,
      widgetLoading,
      analysisName,
      visibility,
      dateFilter,
      widgetsError,
      isAddWidgetModalOpen,
      selectedRack,
      widgetSelectedRacks,
      allWidgetTables,
      isCopyingWidget,
      defaultXCategory,
      sitesData,
      isFetchingSites,
      sitesError,
      tablesData,
      isFetchingTables,
      tablesError,
      columnsData,
      isFetchingColumns,
      columnsError,

      handleOpenAddWidgetModal,
      handleCloseAddWidgetModal,
      setActiveItem,
      handleChangeAnalysisName,
      handleDatesChange,
      handleChangeVisibility,
      handleSelectSite,
      handleSelectTables,
      handleSelectWidget,
      handleClickWidget,
      handleAddNewWidget,
      handleRemoveWidget,
      handleDragEnd,
      handleChangeWidgetName,
      handleSaveWidgets,
      handleSelectRack,
      handleSelectWidgetRack,
      handleResetFilters,
      handleCopyWidget,
      handleSetWidgetSnapshot,
      handleSetYaxisOptions,
      handleRemoveColumnFromWidget,
    ]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 0, // small threshold to avoid click conflict
        delay: 0,
      },
    })
  );

  return (
    <AnalysisTemplateContext.Provider value={value}>
      <DndContext
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        sensors={sensors}
      >
        {/* This will prevent from lagging when dragging over widget */}
        <DisableEchartsPointerEventsOnDrag
          onDragOver={(activeId, overId) => {
            lastOverIds.current = { activeId, overId };
          }}
        />
        {children}
      </DndContext>
    </AnalysisTemplateContext.Provider>
  );
};

export const useAnalysisTemplate = () => {
  const context = useContextSelector(AnalysisTemplateContext, (v) => v);
  if (!context) {
    throw new Error("useAnalysis must be used within AnalysisProvider");
  }
  return context;
};

// Wrapper component with Suspense to handle useSearchParams
export const AnalysisTemplateProviderWithSuspense: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AnalysisTemplateProvider>{children}</AnalysisTemplateProvider>
    </Suspense>
  );
};
