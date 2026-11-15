import React, {
  createContext,
  useContext,
  useState,
  useMemo,
  ReactNode,
  useEffect,
} from "react";
import { useDispatch } from "react-redux";
import {
  useGetSectionOneQuery,
  useGetProcessOverviewTableQuery,
  useGetOperationalStatusDataQuery,
  useGetAreaFilterQuery,
  useGetDailyReportDataQuery,
} from "@/store/api/plantOverviewApi";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { useAppSelector } from "@/hooks";
import { setGlobalSite } from "@/store/slices/siteSelectionSlice";
import dayjs from "dayjs";
import { extractSitesFromClusters } from "../../../../../utils/helpers";

interface PlantOverviewContextType {
  selectedPlant: string;
  setSelectedPlant: (plant: string) => void;
  selectedArea: string;
  setSelectedArea: (area: string) => void;
  selectedDate: string;
  setSelectedDate: (date: string) => void;
  cards: any;
  graph: any;
  from_date: string;
  to_date: string;
  modified: boolean;
  loading: boolean;
  error: any;
  processOverviewTable: any;
  processOverviewTableLoading: boolean;
  processOverviewTableError: any;
  operationalStatusData: any;
  operationalStatusLoading: boolean;
  operationalStatusError: any;
  plants: any[];
  plantsLoading: boolean;
  areaFilter: string[];
  areaFilterLoading: boolean;
  areaFilterError: any;
  dailyReportData: any;
  dailyReportLoading: boolean;
  dailyReportError: any;
}

const PlantOverviewContext = createContext<
  PlantOverviewContextType | undefined
>(undefined);

export const PlantOverviewProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const dispatch = useDispatch();
  const globalSelectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );
  const user = useAppSelector((state) => state.auth.user);

  // Extract available sites from user's role clusters
  const availableSites = useMemo(() => {
    return extractSitesFromClusters(user?.role?.clusters || []);
  }, [user?.role?.clusters]);

  // Initialize with globalSelectedSite if available, otherwise empty string (will be set by useEffect)
  const [selectedPlant, setSelectedPlantState] = useState<string>(
    globalSelectedSite || ""
  );
  const [selectedArea, setSelectedArea] = useState<string>("RO");
  const [selectedDate, setSelectedDate] = useState<string>(
    dayjs(new Date().toString()).format("YYYY-MM-DD")
  );

  // Initialize selectedPlant with first available site if not set
  useEffect(() => {
    // If we have a global selected site, use it
    if (globalSelectedSite && globalSelectedSite !== selectedPlant) {
      setSelectedPlantState(globalSelectedSite);
      return;
    }

    // If no site is selected and we have available sites, use the first one
    if (!selectedPlant && availableSites.length > 0) {
      const firstSite = availableSites[0];
      setSelectedPlantState(firstSite);
      dispatch(setGlobalSite(firstSite));
    }
    // Fallback: if still no site and no available sites, use "UAQ" as last resort
    else if (!selectedPlant && availableSites.length === 0) {
      setSelectedPlantState("UAQ");
      dispatch(setGlobalSite("UAQ"));
    }
  }, [globalSelectedSite, availableSites, selectedPlant, dispatch]);

  // Wrapper to update both local and global state
  const setSelectedPlant = (plant: string) => {
    setSelectedPlantState(plant);
    dispatch(setGlobalSite(plant));
  };

  const { data, isLoading, isFetching, isError } = useGetSectionOneQuery({
    site_id: selectedPlant || "UAQ",
  });

  const {
    data: processOverviewTableData,
    isLoading: processOverviewLoading,
    isFetching: processOverviewTableFetching,
    isError: processOverviewTableError,
  } = useGetProcessOverviewTableQuery({ site_id: selectedPlant || "UAQ" });

  const {
    data: operationalStatusData,
    isLoading: operationalStatusDataLoading,
    isFetching: operationalStatusFetching,
    isError: operationalStatusError,
  } = useGetOperationalStatusDataQuery({
    site_id: selectedPlant || "UAQ",
    area: selectedArea,
  });

  const apiConfigs = useMemo(
    () => [
      {
        key: "process_overview_table",
        name: "Process Overview Table",
        data_availability_for_given_date:
          processOverviewTableData?.data?.modified === true ? false : true,
        from_date: processOverviewTableData?.data?.timestamp,
        to_date: "",
        isLoading: isLoading,
        isFetching: isFetching,
        site_id: selectedPlant,
      },
      {
        key: "operational_status_table",
        name: "Operational Status Table",
        data_availability_for_given_date:
          operationalStatusData?.data?.modified === true ? false : true,
        from_date: operationalStatusData?.data?.from_date,
        to_date: operationalStatusData?.data?.to_date,
        isLoading: operationalStatusDataLoading,
        isFetching: operationalStatusFetching,
        site_id: selectedPlant,
      },
    ],
    [
      processOverviewTableData?.data?.modified,
      processOverviewTableData?.data?.timestamp,
      isLoading,
      isFetching,
      operationalStatusData?.data?.modified,
      operationalStatusData?.data?.from_date,
      operationalStatusData?.data?.to_date,
      operationalStatusDataLoading,
      operationalStatusFetching,
      selectedPlant,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });
  // Fetch area filter data
  const {
    data: areaFilterData,
    isLoading: areaFilterLoading,
    isError: areaFilterError,
  } = useGetAreaFilterQuery({ site_id: selectedPlant || "UAQ" });

  // Daily report query
  const {
    data: dailyReportRaw,
    isLoading: dailyReportDataLoading,
    isFetching: dailyReportFetching,
    isError: dailyReportError,
  } = useGetDailyReportDataQuery({
    site_id: selectedPlant || "UAQ",
    date: selectedDate || "",
  });

  const loading = isLoading || isFetching;

  const processOverviewTableLoading =
    processOverviewLoading || processOverviewTableFetching;

  const operationalStatusLoading =
    operationalStatusDataLoading || operationalStatusFetching;
  const dailyReportLoading = dailyReportDataLoading || dailyReportFetching;

  const value = useMemo(
    () => ({
      selectedPlant,
      setSelectedPlant,
      selectedArea,
      setSelectedArea,
      selectedDate,
      setSelectedDate,
      cards: data?.data?.cards ?? null,
      graph: data?.data?.graph ?? null,
      from_date: data?.data?.from_date ?? "",
      to_date: data?.data?.to_date ?? "",
      modified: data?.data?.modified ?? false,
      loading: loading,
      error: isError,
      processOverviewTable: processOverviewTableData,
      processOverviewTableLoading,
      processOverviewTableError,
      operationalStatusData: operationalStatusData,
      operationalStatusLoading,
      operationalStatusError,
      plants: [], // Provide an empty array or fetch logic if available
      plantsLoading: false, // Provide a default loading state or fetch logic if available
      areaFilter: areaFilterData?.data ?? [],
      areaFilterLoading,
      areaFilterError,
      dailyReportData: dailyReportRaw?.data,
      dailyReportLoading,
      dailyReportError,
    }),
    [
      selectedPlant,
      selectedArea,
      selectedDate,
      data,
      loading,
      isError,
      processOverviewTableData,
      processOverviewTableLoading,
      processOverviewTableError,
      operationalStatusData,
      operationalStatusLoading,
      operationalStatusError,
      areaFilterData,
      areaFilterLoading,
      areaFilterError,
      dailyReportRaw,
      dailyReportLoading,
      dailyReportError,
      setSelectedPlant,
    ]
  );

  return (
    <PlantOverviewContext.Provider value={value}>
      {children}
    </PlantOverviewContext.Provider>
  );
};

export const usePlantOverviewContext = () => {
  const ctx = useContext(PlantOverviewContext);
  if (!ctx)
    throw new Error(
      "usePlantOverviewContext must be used within PlantOverviewProvider"
    );
  return ctx;
};
