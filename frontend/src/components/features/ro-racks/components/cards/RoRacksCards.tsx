"use client";
import React, { FC } from "react";

// ✅ Updated to allow string | number
type CardItem = { value: number | string; unit: string; percent: number };

type Props = {
  pass: "firstPass" | "secondPass";
  cards: Record<string, CardItem>;
  loading?: boolean;
};

const RoRacksCards: FC<Props> = ({ cards, pass }) => {
  const preparedCards = Object.entries(cards).reduce<
    Record<string, { value: number | string; unit: string; percent: number }>
  >((acc, [key, item]) => {
    if (key.toLowerCase().includes("percent")) {
      const mainKey = key.replace(/ percent$/i, "");
      if (acc[mainKey]) {
        // ✅ Handle string values for percent
        acc[mainKey].percent = typeof item.value === "number" ? item.value : 0;
      }
    } else {
      acc[key] = { ...item, percent: item.percent ?? 0 };
    }
    return acc;
  }, {});

  const formatKey = (key: string) => {
    return key
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      .split(" ")
      .map((word) =>
        word.length <= 2
          ? word.toUpperCase()
          : word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(" ");
  };

  const getBackgroundColor = (key: string) => {
    const lowerKey = key.toLowerCase();

    if (pass === "firstPass") {
      if (lowerKey.includes("permeate")) return "#ECF6FE";
      if (lowerKey.includes("sec")) return "#DEF8EA";
    } else {
      if (lowerKey.includes("permeate")) return "#F0F4FF";
      if (lowerKey.includes("sec")) return "#FFEBF2";
    }

    return "#F9FAFB";
  };

  return (
    <div className="mb-3 flex gap-3">
      {Object.entries(preparedCards).map(([key, { value, unit, percent }]) => (
        <div
          key={key}
          style={{ backgroundColor: getBackgroundColor(key) }}
          className="flex flex-1 items-center justify-between rounded-2xl px-6 py-5 shadow-sm"
        >
          <p className="text-lg font-bold text-gray-700">{formatKey(key)}</p>
          <p className="text-lg font-bold text-gray-800">
            {value} {unit}{" "}
            <span className="font-medium text-gray-500">({percent}%)</span>
          </p>
        </div>
      ))}
    </div>
  );
};

export default RoRacksCards;
