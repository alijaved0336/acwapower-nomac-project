"use client";

import React, {
  useMemo,
  useState,
  useTransition,
  useRef,
  useEffect,
} from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import {
  useGetConductivitiesPass1Query,
  useGetConductivitiesPass2Query,
} from "@/store/api/racksWeightedApi";
import { EBarChart } from "../../../../common/charts";
import YAxisConfiguratorModal from "../../../../common/modals/YAxisConfiguratorModal";
import { Alert, Card } from "antd";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
} from "../../../../../utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { ColumnData } from "@/types/analysis.types";
import Spinner from "../../../../common/Spinner";
import { useApiNotifications } from "@/hooks/useApiNotifications";

const ConductivitiesCharts: React.FC = () => {
  const { selectedFilters, selectedRacks, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const hasLoadedOnce = useRef(false);

  const racksParam =
    selectedRacks.length > 0
      ? selectedRacks.map((rack) => `${rack}`).join(",")
      : undefined;

  // Queries
  const {
    data: pass1Response,
    isLoading: pass1Loading,
    isFetching: pass1Fetching,
    error: pass1Error,
  } = useGetConductivitiesPass1Query(
    {
      site_name: selectedSite || "",
      stream: selectedFilters.stream || undefined,
      racks: racksParam,
      from_date: selectedFilters.dateRange?.[0]?.format(
        "YYYY-MM-DDTHH:mm:ss[Z]"
      ),
      to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DDTHH:mm:ss[Z]"),
    },
    { skip: !selectedSite }
  );
  const {
    data: pass2Response,
    isLoading: pass2Loading,
    isFetching: pass2Fetching,
    error: pass2Error,
  } = useGetConductivitiesPass2Query(
    {
      site_name: selectedSite || "",
      stream: selectedFilters.stream || undefined,
      racks: racksParam,
      from_date: selectedFilters.dateRange?.[0]?.format(
        "YYYY-MM-DDTHH:mm:ss[Z]"
      ),
      to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DDTHH:mm:ss[Z]"),
    },
    { skip: !selectedSite }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "pass1",
        name: "1st Pass Conductivities",
        data_availability_for_given_date:
          pass1Response?.data_availability_for_given_date,
        from_date: pass1Response?.from_date,
        to_date: pass1Response?.to_date,
        isLoading: pass1Loading,
        isFetching: pass1Fetching,
      },
      {
        key: "pass2",
        name: "2nd Pass Conductivities",
        data_availability_for_given_date:
          pass2Response?.data_availability_for_given_date,
        from_date: pass2Response?.from_date,
        to_date: pass2Response?.to_date,
        isLoading: pass2Loading,
        isFetching: pass2Fetching,
      },
    ],
    [
      pass1Response?.data_availability_for_given_date,
      pass1Response?.from_date,
      pass1Response?.to_date,
      pass1Loading,
      pass1Fetching,
      pass2Response?.data_availability_for_given_date,
      pass2Response?.from_date,
      pass2Response?.to_date,
      pass2Loading,
      pass2Fetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  // Notifications will NOT stack (appear vertically one below another)
  const pass1Data = useMemo(
    () =>
      Array.isArray(pass1Response?.data)
        ? (pass1Response?.data as ColumnData[])
        : [],
    [pass1Response]
  );

  const pass2Data = useMemo(
    () =>
      Array.isArray(pass2Response?.data)
        ? (pass2Response?.data as ColumnData[])
        : [],
    [pass2Response]
  );
  useEffect(() => {
    if (hasInitiallyLoaded && (pass1Data.length > 0 || pass2Data.length > 0)) {
      hasLoadedOnce.current = true;
    }
  }, [pass1Data, pass2Data, hasInitiallyLoaded]);

  const [isPass1ConfigOpen, setIsPass1ConfigOpen] = useState(false);
  const [pass1YaxisOptions, setPass1YaxisOptions] = useState<
    EChartsYAxisConfig[]
  >([]);
  const [isPending1, startTransition1] = useTransition();

  const [isPass2ConfigOpen, setIsPass2ConfigOpen] = useState(false);
  const [pass2YaxisOptions, setPass2YaxisOptions] = useState<
    EChartsYAxisConfig[]
  >([]);
  const [isPending2, startTransition2] = useTransition();

  const { numericColumns: pass1NumericCols, ranges: pass1Ranges } =
    useYAxisConfigurator(pass1Data);
  const { numericColumns: pass2NumericCols, ranges: pass2Ranges } =
    useYAxisConfigurator(pass2Data);

  const pass1NumericCount = useMemo(() => {
    return pass1Data.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [pass1Data]);

  const pass2NumericCount = useMemo(() => {
    return pass2Data.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [pass2Data]);

  const handlePass1Save = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition1(() => {
      if (Array.isArray(config)) setPass1YaxisOptions(config);
    });
    setIsPass1ConfigOpen(false);
  };

  const handlePass2Save = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition2(() => {
      if (Array.isArray(config)) setPass2YaxisOptions(config);
    });
    setIsPass2ConfigOpen(false);
  };

  const showSpinner =
    (pass1Loading || pass2Loading || pass1Fetching || pass2Fetching) &&
    hasLoadedOnce.current;

  if (pass1Error || pass2Error) {
    return (
      <div className="flex min-h-[600px] items-center justify-center">
        <Alert
          message="Error loading conductivities data"
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <>
      {isPass1ConfigOpen && (
        <YAxisConfiguratorModal
          selectedOptions={pass1YaxisOptions}
          numericColumns={pass1NumericCols}
          ranges={pass1Ranges}
          open={isPass1ConfigOpen}
          columns={pass1Data}
          chartType="bar"
          onCancel={() => setIsPass1ConfigOpen(false)}
          onSave={handlePass1Save}
        />
      )}

      {isPass2ConfigOpen && (
        <YAxisConfiguratorModal
          selectedOptions={pass2YaxisOptions}
          numericColumns={pass2NumericCols}
          ranges={pass2Ranges}
          open={isPass2ConfigOpen}
          columns={pass2Data}
          chartType="bar"
          onCancel={() => setIsPass2ConfigOpen(false)}
          onSave={handlePass2Save}
        />
      )}

      {/* 1st Pass Card */}
      <Card>
        {showSpinner && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/80">
            <Spinner />
          </div>
        )}

        <div
          style={{
            opacity: isPending1 ? 0.5 : 1,
            transition: "opacity 0.2s ease",
          }}
        >
          {isPending1 && (
            <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/80">
              <Spinner />
            </div>
          )}
          <EBarChart
            columns={pass1Data}
            title="1st Pass Conductivities"
            orientation="vertical"
            yaxisOptions={pass1YaxisOptions}
            stack="total"
            onOpenYaxisModal={() => setIsPass1ConfigOpen(true)}
            columnsLength={pass1NumericCount}
            showZoomControls={true}
            showMenu={true}
          />
        </div>
      </Card>

      {/* 2nd Pass Card */}
      <Card>
        <div
          style={{
            opacity: isPending2 ? 0.5 : 1,
            transition: "opacity 0.2s ease",
          }}
        >
          {isPending2 && (
            <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/80">
              <Spinner />
            </div>
          )}
          <EBarChart
            columns={pass2Data}
            title="2nd Pass Conductivities"
            orientation="vertical"
            yaxisOptions={pass2YaxisOptions}
            onOpenYaxisModal={() => setIsPass2ConfigOpen(true)}
            columnsLength={pass2NumericCount}
            showZoomControls={true}
            showMenu={true}
          />
        </div>
      </Card>
    </>
  );
};

export default ConductivitiesCharts;
