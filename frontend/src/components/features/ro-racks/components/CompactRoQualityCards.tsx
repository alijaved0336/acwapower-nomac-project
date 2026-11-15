"use client";

import React, { useMemo } from "react";
import { useGetRoRacksDataQuery } from "@/store/api/roRacksApi";
import { useRoRacksContext } from "../context/RoRacksContext";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import { arrayToCardObject, CardItem } from "../utils/roRacksUtils";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { Skeleton, theme } from "antd";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { useAppSelector } from "@/hooks";
import { cn } from "@/utils/cn";
import styles from "../styles/compactRoQualityCards.module.css";

interface CompactRoQualityCardsProps {
  pass: "firstPass" | "secondPass";
  loading?: boolean;
  cardType?: "temperature" | "conductivity" | "phOrConductivity";
}

const CompactRoQualityCard: React.FC<{
  title: string;
  value: string | number;
  unit: string;
  color: { bg: string; text: string };
  loading?: boolean;
  isUAQ?: boolean;
}> = ({ title, value, unit, color, loading, isUAQ = false }) => {
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const { token } = theme.useToken();

  // Dark mode background - original gradient
  const darkBg = "linear-gradient(135deg, #1F2937 0%, #374151 100%)";

  if (loading) {
    return (
      <div
        className={cn(styles.loadingCard, isUAQ && styles.loadingCardUAQ)}
        style={{
          background: isDark ? darkBg : undefined,
          border: `1px solid ${token.colorBorder}`,
          boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
        }}
      >
        <div className={cn(styles.loadingBar, styles.loadingBarTitle)} />
        <div className={cn(styles.loadingBar, styles.loadingBarValue)} />
      </div>
    );
  }

  return (
    <div
      className={cn(styles.card, isUAQ && styles.cardUAQ)}
      style={{
        background: isDark ? darkBg : color.bg,
        border: `1px solid ${token.colorBorder}`,
        boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
      }}
    >
      <span
        className={styles.title}
        style={{
          color: isDark ? token.colorText : color.text,
          opacity: isDark ? 1 : 0.9,
        }}
      >
        {title}
      </span>
      <div className={styles.cardContent}>
        <span
          className={styles.value}
          style={{
            color: isDark ? token.colorText : color.text,
            opacity: isDark ? 1 : 1,
          }}
        >
          {value}
        </span>
        <span
          className={styles.unit}
          style={{
            color: isDark ? token.colorTextSecondary : color.text,
            opacity: isDark ? 1 : 0.7,
          }}
        >
          {unit}
        </span>
      </div>
    </div>
  );
};

const CompactRoQualityCards: React.FC<CompactRoQualityCardsProps> = ({
  pass,
  loading = false,
  cardType,
}) => {
  const { selectedFilters, selectedSite } = useRoRacksContext();
  const site_name = selectedSite || selectedFilters?.plant;
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");
  const siteDisplayName = getSiteDisplayName(site_name || "");
  const isUAQ =
    siteDisplayName === "Umm Al Quwain IWP" ||
    site_name === "UAQ" ||
    site_name === "uaq";
  const isJubail =
    siteDisplayName === "Jubail 3A IWP" ||
    site_name === "Jubail-Jazlah" ||
    site_name === "jazla" ||
    site_name === "jubail";

  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const { token } = theme.useToken();

  // Fetch data
  const { data, isLoading, error } = useGetRoRacksDataQuery(
    { site_name, selectedDate, pass },
    {
      selectFromResult: ({ data, isFetching, isLoading, error }) => ({
        data,
        isLoading: isFetching || isLoading,
        error,
      }),
      skip: !site_name || !selectedDate,
    }
  );

  // Extract cards data
  const allCards = useMemo(
    () => (Array.isArray(data?.data?.cards) ? data.data.cards : []),
    [data]
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
        site_id: selectedSite,
      },
    ],
    [
      data?.data.data_availability_for_given_date,
      data?.data.from_date,
      data?.data.to_date,
      isLoading,
      selectedSite,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });
  const streamList = ["Stream1", "Stream2", "Stream3"];

  // Quality Cards Filtering - determine card names based on endpoint data
  // Pass 1: RO Inlet Temp, RO Inlet Conductivity, Permeate Conductivity
  // Pass 2: RO Inlet Temp, RO Inlet Conductivity, RO pH, Permeate Conductivity
  const roQualityCardNames = isUAQ
    ? streamList.flatMap((stream) =>
        pass === "firstPass"
          ? [
              `${stream} RO Inlet Temperature`,
              `${stream} RO Inlet Conductivity`,
              `${stream} Conductivity`, // Permeate Conductivity
            ]
          : [
              `${stream} RO Inlet Temperature`,
              `${stream} RO Inlet Conductivity`,
              `${stream} Ph`, // RO pH
              `${stream} Conductivity`, // Permeate Conductivity
            ]
      )
    : pass === "firstPass"
      ? [
          "RO Inlet Temperature", // RO Inlet Temp
          "RO Inlet Conductivity",
          "Conductivity", // Permeate Conductivity
        ]
      : [
          "RO Inlet Temperature", // RO Inlet Temp
          "RO Inlet Conductivity",
          "Ph", // RO pH
          "Conductivity", // Permeate Conductivity
        ];

  // Convert to Card Object
  const qualityCardsObj: Record<string, CardItem> = useMemo(
    () =>
      arrayToCardObject(
        allCards.filter((item) => roQualityCardNames.includes(item.columnName))
      ),
    [allCards, roQualityCardNames]
  );

  const isDataLoading = loading || isLoading;

  if (error) {
    return (
      <div className={styles.errorContainer}>
        Failed to load RO Quality data
      </div>
    );
  }

  // Filter cards based on cardType (for backward compatibility)
  const getCardForType = (type: string) => {
    const cardMap: Record<string, string> = {
      temperature: isUAQ
        ? "Stream1 RO Inlet Temperature"
        : "RO Inlet Temperature",
      conductivity: isUAQ
        ? "Stream1 RO Inlet Conductivity"
        : "RO Inlet Conductivity",
      phOrConductivity:
        pass === "firstPass"
          ? isUAQ
            ? "Stream1 Conductivity"
            : "Conductivity"
          : isUAQ
            ? "Stream1 Ph"
            : "Ph",
    };

    const cardKey = cardMap[type];
    return qualityCardsObj[cardKey];
  };

  const cardColors = {
    temperature: { bg: "#dbeafe", text: "#1e40af" }, // Blue (overall)
    conductivity: { bg: "#e0f2fe", text: "#0c4a6e" }, // Green (firstPass)
    phOrConductivity: { bg: "#fae8ff", text: "#86198f" }, // Purple (secondPass)
  };

  const cardTitles = {
    temperature: "RO Inlet Temperature",
    conductivity: "RO Inlet Conductivity",
    phOrConductivity: pass === "firstPass" ? "Conductivity" : "Ph",
  };

  // If cardType is specified, show only that card (for backward compatibility)
  if (cardType) {
    const card = getCardForType(cardType);
    const title = cardTitles[cardType];

    if (isDataLoading) {
      return (
        <div className={styles.singleCardLoading}>
          <Skeleton active paragraph={{ rows: 1 }} style={{ width: "80%" }} />
        </div>
      );
    }

    if (!card) {
      return (
        <div className={styles.errorContainerSingle}>
          No {title} data available
        </div>
      );
    }

    return (
      <CompactRoQualityCard
        title={title}
        value={card.value}
        unit={card.unit || ""}
        color={cardColors[cardType]}
        loading={isDataLoading}
        isUAQ={isUAQ}
      />
    );
  }

  // Helper function to format card title
  const getCardTitle = (name: string): string => {
    // Check if it has a stream prefix (for UAQ)
    const streamMatch = name.match(/^(Stream\d+)\s*(.*)/i);

    if (streamMatch) {
      // UAQ case - preserve stream prefix
      const streamPrefix = streamMatch[1];
      const cleanName = streamMatch[2].trim();

      // Format the clean name part
      let formattedName = cleanName;
      if (cleanName === "RO Inlet Temperature") formattedName = "RO Inlet Temp";
      else if (cleanName === "RO Inlet Conductivity")
        formattedName = "RO Inlet Conductivity";
      else if (cleanName === "Ph") formattedName = "RO pH";
      else if (cleanName === "Conductivity")
        formattedName = "Permeate Conductivity";

      return `${streamPrefix} ${formattedName}`;
    } else {
      // Jubail case - no stream prefix
      if (name === "RO Inlet Temperature") return "RO Inlet Temp";
      if (name === "RO Inlet Conductivity") return "RO Inlet Conductivity";
      if (name === "Ph") return "RO pH";
      if (name === "Conductivity") return "Permeate Conductivity";

      return name;
    }
  };

  // Render all cards: 3 for Pass 1 Jubail, 4 for Pass 2 Jubail, 9 for Pass 1 UAQ, 12 for Pass 2 UAQ
  const cardOrder = isUAQ
    ? streamList.flatMap((stream) => {
        const baseNames =
          pass === "firstPass"
            ? [
                `${stream} RO Inlet Temperature`,
                `${stream} RO Inlet Conductivity`,
                `${stream} Conductivity`,
              ]
            : [
                `${stream} RO Inlet Temperature`,
                `${stream} RO Inlet Conductivity`,
                `${stream} Ph`,
                `${stream} Conductivity`,
              ];
        return baseNames.map((name) => ({
          key: name,
          card: qualityCardsObj[name],
          color:
            name.includes("Temperature") ||
            name.includes("RO Inlet Temperature")
              ? cardColors.temperature
              : name.includes("Ph")
                ? cardColors.phOrConductivity
                : name.includes("Conductivity") && !name.includes("RO Inlet")
                  ? cardColors.phOrConductivity
                  : cardColors.conductivity,
        }));
      })
    : (pass === "firstPass"
        ? [
            "RO Inlet Temperature",
            "RO Inlet Conductivity",
            "Conductivity", // Permeate Conductivity
          ]
        : [
            "RO Inlet Temperature",
            "RO Inlet Conductivity",
            "Ph", // RO pH
            "Conductivity", // Permeate Conductivity
          ]
      ).map((name) => ({
        key: name,
        card: qualityCardsObj[name],
        color:
          name.includes("Temperature") || name.includes("RO Inlet Temperature")
            ? cardColors.temperature
            : name.includes("Ph")
              ? cardColors.phOrConductivity
              : name.includes("Conductivity") && !name.includes("RO Inlet")
                ? cardColors.phOrConductivity
                : cardColors.conductivity,
      }));

  if (isDataLoading) {
    return (
      <div className={cn(styles.container, isUAQ && styles.containerUAQ)}>
        {cardOrder.map((item) => (
          <div
            key={item.key}
            className={cn(
              styles.loadingCard,
              isUAQ && styles.loadingCardUAQ,
              "flex !items-center !justify-between"
            )}
            style={{
              background: isDark ? token.colorBgContainer : item.color.bg,
              border: `1px solid ${token.colorBorder}`,
              boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
            }}
          >
            <Skeleton.Input
              active
              size="small"
              style={{
                width: "60%",
                marginBottom: "8px",
                height: "20px",
              }}
            />
            <Skeleton.Input
              active
              size="small"
              style={{ width: "80%", height: "20px" }}
            />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={cn(styles.container, isUAQ && styles.containerUAQ)}>
      {cardOrder.map((item) => {
        if (!item.card) return null;
        return (
          <CompactRoQualityCard
            key={item.key}
            title={getCardTitle(item.key)}
            value={item.card.value}
            unit={item.card.unit || ""}
            color={item.color}
            loading={isDataLoading}
            isUAQ={isUAQ}
          />
        );
      })}
    </div>
  );
};

export default CompactRoQualityCards;
