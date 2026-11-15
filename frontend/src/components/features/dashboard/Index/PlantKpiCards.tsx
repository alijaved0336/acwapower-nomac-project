"use client";

import { Card, Typography, Skeleton, theme } from "antd";
import type { FC } from "react";
import { Plant } from "../../../../types/energy.types";
import { formatNumber, formatPercentage } from "@/utils/numberUtils";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { cn } from "../../../../utils";

type PlantKpiCardsProps = {
  data: Array<Kpi>;
  selectedPlants?: Array<Plant>;
  selectedPlant?: string;
  allPlants: Array<Plant>;
  loading?: boolean;
  showTotalCard?: boolean;
};

type Kpi = {
  key: number;
  kpi: string;
  total: string;
  units?: string;
  [key: string]: any;
};

type PlantKpi = {
  name: string;
  value: any;
  formattedValue: string;
};

const PlantKpiCards: FC<PlantKpiCardsProps> = ({
  data,
  selectedPlants = [],
  selectedPlant,
  allPlants,
  loading = false,
  showTotalCard = false,
}) => {
  const { token } = theme.useToken();

  const formatKpiValue = (value: any, kpiName: string) => {
    if (value === null || value === undefined || value === "") return "N/A";
    const kpiLower = kpiName.toLowerCase();

    if (typeof value === "string") {
      if (
        ["N/A", "NONE"].includes(value.toUpperCase()) ||
        value.includes("None")
      )
        return "N/A";
      if (kpiLower.includes("quality")) {
        return value.toUpperCase().includes("OK") ? "GOOD" : "BAD";
      }
    }

    let numericValue = value;
    if (typeof value === "string") {
      const numericMatch = value.match(/(\d+(?:\.\d+)?)/);
      if (numericMatch) numericValue = parseFloat(numericMatch[1]);
    }

    if (kpiLower.includes("availability"))
      return formatPercentage(numericValue);
    if (kpiLower.includes("production"))
      return `${formatNumber(numericValue, { decimals: 0 })}m³/h`;
    if (kpiLower.includes("sec")) return `${formatNumber(numericValue)}Kwh/m³`;
    if (kpiLower.includes("power")) return `${formatNumber(numericValue)} kwh`;
    if (!isNaN(parseFloat(numericValue))) return formatNumber(numericValue);

    return String(value);
  };

  const getQualityColor = (value: any) => {
    if (!value) return "default";
    const v = String(value).toLowerCase();
    if (v.includes("ok") || v.includes("good")) return "success";
    if (v.includes("bad") || v.includes("poor")) return "error";
    if (v.includes("risk") || v.includes("warning")) return "warning";
    return "default";
  };

  const getSecColor = (value: any) => {
    if (!value) return "default";
    const num = parseFloat(String(value).replace(/[^\d.]/g, ""));
    return num > 8 ? "warning" : "default";
  };

  const transformPlantKpisToCardData = (plants: Plant[]): Kpi[] => {
    if (!plants.length) return [];
    const allKpiNames = new Set<string>();
    plants.forEach((p) => p.plant_kpis?.forEach((k) => allKpiNames.add(k.kpi)));

    return Array.from(allKpiNames).map((kpiName, index) => {
      const entry: any = { key: index + 1, kpi: kpiName, total: "" };
      plants.forEach((p) => {
        const found = p.plant_kpis?.find((k) => k.kpi === kpiName);
        if (found) {
          const plantKey = String(
            p.plant_type || p.name || p.site_name || p.id
          );
          entry[plantKey] = String(
            found[p.plant_type || p.name || "total"] || "N/A"
          );
          if (found.total && !entry.total) entry.total = String(found.total);
        }
      });
      return entry;
    });
  };

  const hasNewFormat = allPlants?.some((p) => p.plant_kpis?.length);
  const cardData = hasNewFormat
    ? transformPlantKpisToCardData(allPlants)
    : data;

  const allowedKpis = ["production", "sec", "power", "quality"];
  const filteredData = cardData.filter((kpi) =>
    allowedKpis?.some((ak) => kpi.kpi.toLowerCase().includes(ak))
  );

  const getPlantData = () => {
    if (selectedPlant && selectedPlant !== "All Plants") {
      const found = selectedPlants.find(
        (p) =>
          p.id === selectedPlant ||
          p.name === selectedPlant ||
          p.plant_type === selectedPlant ||
          p.site_name === selectedPlant
      );
      return found ? [found] : [];
    }
    return selectedPlants;
  };

  const plantsToShow = allPlants;

  if (loading) {
    return (
      <div
        className="h-[calc(50vh-90px)] overflow-hidden rounded-lg md:h-[360px] lg:h-full"
        style={{ border: `1px solid ${token.colorBorder}` }}
      >
        <div className="flex flex-col gap-4 p-4 md:gap-5 md:p-5">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="rounded-xl border-0 p-3 shadow-sm">
              <Skeleton active paragraph={{ rows: 2 }} />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!filteredData.length || !plantsToShow.length) {
    return (
      <div
        className="flex h-[calc(50vh-90px)] items-center justify-center rounded-lg md:h-[360px] lg:h-full"
        style={{ border: `1px solid ${token.colorBorder}` }}
      >
        <Typography.Text type="secondary">
          No KPI data available
        </Typography.Text>
      </div>
    );
  }

  const createTotalCard = () => (
    <Card
      className="rounded-xl border-0 p-3 shadow-sm"
      style={{
        background: `linear-gradient(135deg, ${token.colorPrimaryBg} 0%, ${token.colorBgContainer} 100%)`,
        borderLeft: `4px solid ${token.colorPrimary}`,
        boxShadow: `0 4px 12px ${token.colorPrimary}15, 0 2px 6px rgba(0, 0, 0, 0.06)`,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Subtle decorative element */}
      <div
        style={{
          position: "absolute",
          top: "-20px",
          right: "-20px",
          width: "80px",
          height: "80px",
          background: `radial-gradient(circle, ${token.colorPrimary}08 0%, transparent 70%)`,
          borderRadius: "50%",
          pointerEvents: "none",
        }}
      />
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: token.colorPrimary,
              boxShadow: `0 0 8px ${token.colorPrimary}60`,
            }}
          />
          <Typography.Text
            strong
            style={{
              fontSize: "20px",
              color: token.colorText,
              letterSpacing: "0.02em",
            }}
          >
            Total
          </Typography.Text>
        </div>
        <div className="!mt-8 space-y-8">
          {filteredData.map((kpi) => {
            const val = formatKpiValue(kpi.total, kpi.kpi);
            const isQuality = kpi.kpi.toLowerCase().includes("quality");
            const isSec = kpi.kpi.toLowerCase().includes("sec");
            const color = isQuality
              ? getQualityColor(kpi.total) === "success"
                ? token.colorSuccess
                : getQualityColor(kpi.total) === "error"
                  ? token.colorError
                  : getQualityColor(kpi.total) === "warning"
                    ? token.colorWarning
                    : token.colorText
              : isSec
                ? getSecColor(kpi.total) === "warning"
                  ? token.colorWarning
                  : token.colorText
                : token.colorText;

            return (
              <div key={kpi.kpi} className="flex items-center justify-between">
                <Typography.Text
                  style={{ fontSize: "14px", color: token.colorTextSecondary }}
                >
                  {kpi.kpi}
                </Typography.Text>
                <Typography.Text
                  style={{ fontSize: "15px", fontWeight: 600, color }}
                >
                  {val}
                </Typography.Text>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );

  const createPlantCards = () =>
    plantsToShow?.map((p, index) => {
      const displayName = getSiteDisplayName(
        p.site_name || p.name || p.plant_type || ""
      );
      const key = String(p.plant_type || p.name || p.site_name || p.id);
      const plantKpis = filteredData.map((kpi) => ({
        name: kpi.kpi,
        value: kpi[key] || kpi.total || "N/A",
        formattedValue: formatKpiValue(kpi[key] || kpi.total || "N/A", kpi.kpi),
      }));

      const isSelectedPlant =
        p.id === selectedPlant ||
        p.name === selectedPlant ||
        p.plant_type === selectedPlant ||
        p.site_name === selectedPlant;

      return (
        <Card
          key={p.id || p.name}
          className={cn("rounded-xl border-0 p-3 shadow-sm", {
            "opacity-50": !isSelectedPlant && !showTotalCard,
          })}
          style={{
            border: `1px solid ${token.colorBorder}`,
            boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
          }}
        >
          <div>
            <Typography.Text
              strong
              style={{ fontSize: "18px", color: token.colorText }}
            >
              {displayName}
            </Typography.Text>
            <div className="!mt-8 space-y-8">
              {plantKpis.map((kpi) => {
                const isQuality = kpi.name.toLowerCase().includes("quality");
                const isSec = kpi.name.toLowerCase().includes("sec");
                const color = isQuality
                  ? getQualityColor(kpi.value) === "success"
                    ? token.colorSuccess
                    : getQualityColor(kpi.value) === "error"
                      ? token.colorError
                      : getQualityColor(kpi.value) === "warning"
                        ? token.colorWarning
                        : token.colorText
                  : isSec
                    ? getSecColor(kpi.value) === "warning"
                      ? token.colorWarning
                      : token.colorText
                    : token.colorText;

                return (
                  <div
                    key={kpi.name}
                    className={cn("flex items-center justify-between")}
                  >
                    <Typography.Text
                      style={{
                        fontSize: "14px",
                        color: token.colorTextSecondary,
                      }}
                    >
                      {kpi.name}
                    </Typography.Text>
                    <Typography.Text
                      style={{ fontSize: "14px", fontWeight: 600, color }}
                    >
                      {kpi.formattedValue}
                    </Typography.Text>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      );
    });

  return (
    <div
      className="h-[calc(50vh-90px)] overflow-hidden rounded-lg md:h-[360px] lg:h-full"
      style={{ border: `1px solid ${token.colorBorder}` }}
    >
      <div className="flex flex-col gap-3 p-3 md:gap-4 md:p-4 lg:gap-5 lg:p-5">
        {showTotalCard && createTotalCard()}
        {createPlantCards()}
      </div>
    </div>
  );
};

export default PlantKpiCards;
