"use client";

import React, { FC, useMemo, useState, useEffect } from "react";
import { Card } from "antd";
import ELineChart from "@/components/common/charts/ELineChart";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "../../../../../hooks/useYAxisConfigurator";
import RoRacksCards from "../cards/RoRacksCards";
import RoRacksCardsUAQ from "../cards/RoRacksCardsUAQ";
import { EChartsYAxisConfig } from "@/utils/chartConfig";
import { useRoRacksContext } from "../../context/RoRacksContext";
import { ColumnData } from "../../../../../types/analysis.types";

// ✅ Updated to match the utils type
type CardItem = { value: number | string; unit: string; percent: number };

type Props = {
  pass: "firstPass" | "secondPass";
  data: { cards: Record<string, CardItem>; chartData: ColumnData[] };
  loading: boolean;
};

const RoRacksChart: FC<Props> = ({ data, pass, loading }) => {
  const { isInitialLoading, selectedFilters, selectedSite } =
    useRoRacksContext();
  const showLoading = loading || isInitialLoading;

  const site_name = selectedSite || selectedFilters?.plant; // Use global site first
  const isUAQ = site_name === "Umm Al Quwain IWP";

  const [modalOpen, setModalOpen] = useState(false);
  const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[]>([]);

  const columns = useMemo(() => data.chartData, [data.chartData]);
  const { numericColumns, ranges } = useYAxisConfigurator(columns);

  useEffect(() => {
    if (!numericColumns.length) return;

    // ✅ Default config for non-UAQ sites
    let defaultConfig: EChartsYAxisConfig[] =
      pass === "firstPass"
        ? [
            { seriesName: "Pass 1 Permeate Flow", show: true, opposite: false },
            { seriesName: "Pass 1 SEC", show: true, opposite: true },
          ]
        : [
            { seriesName: "Pass 2 Permeate Flow", show: true, opposite: false },
            { seriesName: "Pass 2 SEC", show: true, opposite: true },
          ];

    // ✅ Custom config for UAQ
    if (isUAQ) {
      const streams = ["Stream1", "Stream2", "Stream3"];
      const flowSeries = streams.map((s) => ({
        seriesName: `${s} ${pass === "firstPass" ? "Pass 1" : "Pass 2"} Permeate Flow`,
        show: true,
        opposite: false,
      }));
      const secSeries = streams.map((s) => ({
        seriesName: `${s} ${pass === "firstPass" ? "Pass 1" : "Pass 2"} SEC`,
        show: true,
        opposite: true,
      }));
      defaultConfig = [...flowSeries, ...secSeries];
    }

    setYAxisConfig(defaultConfig);
  }, [numericColumns, pass, isUAQ]);

  return (
    <div className="space-y-6">
      <Card variant="borderless" className="rounded-2xl p-6 shadow-sm">
        {isUAQ ? (
          <RoRacksCardsUAQ
            pass={pass}
            cards={data.cards}
            loading={showLoading}
          />
        ) : (
          <RoRacksCards pass={pass} cards={data.cards} loading={showLoading} />
        )}

        <ELineChart
          columns={columns}
          height="55vh"
          yAxisConfig={yAxisConfig}
          loading={showLoading}
          onOpenYaxisModal={() => setModalOpen(true)}
        />
      </Card>

      {/* Y-Axis Configurator Modal */}
      <YAxisConfiguratorModal
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onSave={(config) => {
          if (Array.isArray(config)) setYAxisConfig(config);
          setModalOpen(false);
        }}
        selectedOptions={yAxisConfig}
        numericColumns={numericColumns}
        ranges={ranges}
        columns={columns}
        chartType="line"
        widgetId={`ro-racks-${pass}`}
      />
    </div>
  );
};

export default RoRacksChart;
